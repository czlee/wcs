#!/usr/bin/env python3
"""One-off experiment: do event-cluster bootstrap intervals differ from the site's ±1.96·SE bars?

NOT part of the pipeline: nothing imports this, and the site doesn't use its output. It is
kept as a record of an analysis, so that the question doesn't have to be re-derived.

Why
---
The site's error bars (site/src/lib/stats.js ``meanCI``) are mean ± 1.96·SD/√n, which treats
every scoresheet as independent. They aren't: judges sit on many panels, and divisions
share events. The Limitations box says the bars are therefore "probably too narrow". The
question here was whether resampling whole *events* (a cluster bootstrap) would change the
picture enough to be worth building into the site (precomputed intervals plus a live
in-browser fallback for filters).

What it computes
----------------
Reads data/metrics.csv only; touches nothing in site/. Scope matches the site: J&J and
Strictly finals at the six levels, the 12 metrics in export_site_data.METRICS, native metric
direction, and the top-3 metrics only counting finals of 6 or more (mirrors
site/src/lib/families.js ``minN``). For every format x level x metric group it computes three
95% intervals for the mean:

  existing   mean +/- 1.96 * SD / sqrt(n), SD with ddof = 1 (identical to ``meanCI``)
  sheet-bs   percentile bootstrap resampling scoresheets (a control: shows whether the
             percentile-vs-normal choice alone moves anything)
  event-bs   percentile bootstrap resampling whole events. Each resample is a multinomial
             count vector over the format's events; a level's mean is (W.S)/(W.N), with S and
             N the per-event sum and count of that level's sheets.

For adjacent levels it also compares the difference of means: an independent normal interval
(+/- 1.96 * sqrt(SE_a^2 + SE_b^2)) against the paired event-bootstrap interval, where the
same resampled events feed both levels (so shared-event correlation is respected).

Outputs: data/interval-comparison.csv (one row per group), data/interval-comparison-diffs.csv
(one row per adjacent-level difference) and a printed summary. A second seed is run to report
Monte-Carlo noise, and all-ones weights are asserted to reproduce the plain mean.

Result (data as of 1,672 sheets / 254 events, B = 20,000)
---------------------------------------------------------
- Single-level bars: event-bs width / existing width has median 1.00 (range 0.97-1.06). This
  is expected: within one format and level almost every event has exactly one sheet, so
  resampling events is the same as resampling sheets.
- Adjacent-level differences: paired event-bs is a median 0.95 x the independent width
  (range 0.63-1.07), narrower where adjacent levels' means are positively correlated across
  events. The effect is mostly J&J rank-spread metrics (sd_rank, mean abs. rank deviation:
  correlation ~0.28, ~15% narrower, up to 37%), plausibly because field size is shared within
  an event. 1 of 120 differences changes whether its interval excludes 0; bar overlap between
  adjacent levels doesn't change at all.
- Groups with fewer than 20 events (Strictly Newcomer: 8) are too small for a cluster bootstrap.
- Monte-Carlo noise: endpoints move at most ~0.08 x SE between seeds.

Conclusion: resampling events does little for the single-level bars. The dependence that matters
more is shared judges (about 1,100 distinct judges; ~73% of judge slots belong to judges on 10+
sheets; the judge-sheet graph is one connected component, so there are no clean judge clusters
to resample). Handling that needs crossed random effects (judge, event) -- see Phase 5 in
plan.md. If the site ever shows level differences, the paired event bootstrap is the right
interval for them.

Usage: python scripts/compare_intervals.py [--reps 20000] [--seed 1]   (from scripts/, in the venv)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from export_site_data import FORMATS, LEVELS, METRICS

DATA_DIR = Path(__file__).parent.parent / "data"
# Mirrors site/src/lib/families.js: the top-3 metrics only count finals of 6 or more.
MIN_N = {"overlap_at_3_cc": 6, "jaccard_at_3_cc": 6, "overlap_at_3": 6, "jaccard_at_3": 6}
MIN_EVENTS = 20  # fewer events than this and a cluster bootstrap is unreliable
Z = 1.96


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "metrics.csv")
    df = df[df["dance_format"].isin(FORMATS) & df["division_level"].isin(LEVELS)].copy()
    assert df["event_id"].notna().all(), "scoresheets without an event_id"
    return df


def sheet_bootstrap(vals: np.ndarray, reps: int, rng: np.random.Generator) -> tuple[float, float]:
    n = len(vals)
    means = np.empty(reps)
    for i in range(0, reps, 2000):  # chunked to bound memory
        k = min(2000, reps - i)
        means[i:i + k] = vals[rng.integers(0, n, size=(k, n))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def run(df: pd.DataFrame, reps: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    rows, diffs = [], []
    for fname in FORMATS:
        fdf = df[df["dance_format"] == fname]
        events = fdf["event_id"].unique()
        e_idx = {e: i for i, e in enumerate(events)}
        E = len(events)
        # One set of resampled events per format, shared by every level and metric, so level
        # differences are paired (an event drawn twice counts twice for every level).
        W = rng.multinomial(E, np.full(E, 1 / E), size=reps).astype(np.float64)
        for metric in METRICS:
            S, N, plain = {}, {}, {}
            info = {}
            for level in LEVELS:
                g = fdf[(fdf["division_level"] == level)
                        & (fdf["num_competitors"] >= MIN_N.get(metric, 0))]
                vals = g[metric].to_numpy(float)
                ei = g["event_id"].map(e_idx).to_numpy()
                S[level] = np.bincount(ei, weights=vals, minlength=E)
                N[level] = np.bincount(ei, minlength=E).astype(float)
                # Fixed-weights check: all-ones weights reproduce the plain mean.
                if len(vals):
                    assert np.isclose(S[level].sum() / N[level].sum(), vals.mean())
                plain[level] = vals
                info[level] = (len(vals), g["event_id"].nunique())
            means = {}
            with np.errstate(invalid="ignore", divide="ignore"):
                for level in LEVELS:
                    means[level] = (W @ S[level]) / (W @ N[level])
            ci = {}
            for level in LEVELS:
                vals = plain[level]
                n, n_events = info[level]
                mu = float(vals.mean()) if n else np.nan
                se = float(vals.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
                ex_lo, ex_hi = mu - Z * se, mu + Z * se
                ev_lo, ev_hi = np.nanpercentile(means[level], [2.5, 97.5]) if n else (np.nan,) * 2
                sh_lo, sh_hi = sheet_bootstrap(vals, reps, rng) if n > 1 else (np.nan, np.nan)
                ci[level] = dict(mean=mu, se=se, lo=ex_lo, hi=ex_hi)
                rows.append(dict(
                    format=fname, level=level, metric=metric, n=n, events=n_events, mean=mu, se=se,
                    ex_lo=ex_lo, ex_hi=ex_hi, sh_lo=sh_lo, sh_hi=sh_hi, ev_lo=ev_lo, ev_hi=ev_hi,
                ))
            names = list(LEVELS)
            for a, b in zip(names[:-1], names[1:]):  # adjacent levels, difference b - a
                if info[a][0] < 2 or info[b][0] < 2:
                    continue
                d = ci[b]["mean"] - ci[a]["mean"]
                half = Z * np.sqrt(ci[a]["se"] ** 2 + ci[b]["se"] ** 2)
                dd = means[b] - means[a]
                ev_lo, ev_hi = np.nanpercentile(dd, [2.5, 97.5])
                diffs.append(dict(
                    format=fname, metric=metric, a=a, b=b, n_a=info[a][0], n_b=info[b][0],
                    events_a=info[a][1], events_b=info[b][1], diff=d,
                    ex_lo=d - half, ex_hi=d + half, ev_lo=ev_lo, ev_hi=ev_hi,
                    corr=float(np.corrcoef(means[a][np.isfinite(dd)], means[b][np.isfinite(dd)])[0, 1]),
                ))
    out, dout = pd.DataFrame(rows), pd.DataFrame(diffs)
    for t in (out,):
        t["ex_w"], t["sh_w"], t["ev_w"] = (t["ex_hi"] - t["ex_lo"], t["sh_hi"] - t["sh_lo"], t["ev_hi"] - t["ev_lo"])
        t["sh_ratio"], t["ev_ratio"] = t["sh_w"] / t["ex_w"], t["ev_w"] / t["ex_w"]
    dout["ex_w"], dout["ev_w"] = dout["ex_hi"] - dout["ex_lo"], dout["ev_hi"] - dout["ev_lo"]
    dout["ratio"] = dout["ev_w"] / dout["ex_w"]
    return out, dout


def spread(s: pd.Series) -> str:
    return f"{s.median():.2f}  ({s.min():.2f}-{s.max():.2f})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    df = load()
    print(f"{len(df)} scoresheets, {df['event_id'].nunique()} events; B = {args.reps}, seed = {args.seed}")
    out, dout = run(df, args.reps, args.seed)
    out2, _ = run(df, args.reps, args.seed + 1)
    out.to_csv(DATA_DIR / "interval-comparison.csv", index=False)
    dout.to_csv(DATA_DIR / "interval-comparison-diffs.csv", index=False)

    # Monte-Carlo noise: how far do bootstrap endpoints move between seeds, relative to the SE?
    for col in ("sh_lo", "sh_hi", "ev_lo", "ev_hi"):
        shift = ((out[col] - out2[col]).abs() / out["se"]).max()
        print(f"  largest {col} change between seeds: {shift:.3f} x SE")

    big = out[out["events"] >= MIN_EVENTS]
    small = out[out["events"] < MIN_EVENTS]
    print(f"\n== Interval width relative to the existing mean +/- 1.96 SE: median (min-max) over the "
          f"{len(big) // len(METRICS)} format x level groups with >= {MIN_EVENTS} events ==")
    print(f"{'metric':26s} {'sheet-bs / existing':>22s} {'event-bs / existing':>22s}")
    for m in METRICS:
        g = big[big["metric"] == m]
        print(f"{m:26s} {spread(g['sh_ratio']):>22s} {spread(g['ev_ratio']):>22s}")
    print(f"{'ALL':26s} {spread(big['sh_ratio']):>22s} {spread(big['ev_ratio']):>22s}")
    print(f"\n   event-bs / existing by format and level (median over metrics):")
    print(big.pivot_table(index="level", columns="format", values="ev_ratio", aggfunc="median")
          .reindex(list(LEVELS)).round(3).to_string())

    print(f"\n== Groups with fewer than {MIN_EVENTS} events (interval would be suppressed) ==")
    for (f, l), g in small.groupby(["format", "level"]):
        print(f"  {f} {l}: {int(g['events'].median())} events; "
              f"event-bs / existing median {g['ev_ratio'].median():.2f}")

    print("\n== Adjacent-level differences (paired event-bs width / independent existing width) ==")
    print(f"{'metric':26s} {'ratio':>22s}")
    for m in METRICS:
        print(f"{m:26s} {spread(dout[dout['metric'] == m]['ratio']):>22s}")
    print(f"{'ALL':26s} {spread(dout['ratio']):>22s}")
    print(f"   mean correlation of adjacent levels' resampled means: {dout['corr'].mean():.3f} "
          f"(range {dout['corr'].min():.3f} to {dout['corr'].max():.3f})")

    ex0 = (dout["ex_lo"] > 0) | (dout["ex_hi"] < 0)
    ev0 = (dout["ev_lo"] > 0) | (dout["ev_hi"] < 0)
    print(f"\n   differences whose interval excludes 0: existing {ex0.sum()} / {len(dout)}, "
          f"event-bs {ev0.sum()} / {len(dout)}; conclusions that differ: {(ex0 != ev0).sum()}")
    chg = dout[ex0 != ev0][["format", "metric", "a", "b", "diff", "ex_lo", "ex_hi", "ev_lo", "ev_hi"]]
    if len(chg):
        print(chg.round(4).to_string(index=False))

    # Whether the single-level bars of adjacent levels overlap, existing vs event-bs.
    ov_ex = ov_ev = changed = 0
    for (f, m), g in out.groupby(["format", "metric"]):
        g = g.set_index("level").reindex(list(LEVELS))
        for a, b in zip(list(LEVELS)[:-1], list(LEVELS)[1:]):
            if g.loc[[a, b], "n"].min() < 2:
                continue
            o_ex = not (g.loc[a, "ex_hi"] < g.loc[b, "ex_lo"] or g.loc[b, "ex_hi"] < g.loc[a, "ex_lo"])
            o_ev = not (g.loc[a, "ev_hi"] < g.loc[b, "ev_lo"] or g.loc[b, "ev_hi"] < g.loc[a, "ev_lo"])
            ov_ex += o_ex
            ov_ev += o_ev
            changed += o_ex != o_ev
    print(f"\n   adjacent-level bars that overlap: existing {ov_ex}, event-bs {ov_ev}; pairs that differ: {changed}")
    print(f"\nWrote {DATA_DIR / 'interval-comparison.csv'} and {DATA_DIR / 'interval-comparison-diffs.csv'}")


if __name__ == "__main__":
    main()
