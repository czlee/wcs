#!/usr/bin/env python3
"""Phase 3: Compute inter-judge agreement metrics from parsed scoresheets.

Reads every data/parsed/{id}.json (Phase 2 output), computes a panel of rank-based
agreement metrics from each scoresheet's judge x competitor rank matrix, and writes
one row per scoresheet to data/metrics.csv.

Governing principle (see briefs/phase-3-implementation-brief.md): store RAW metric
values plus only transforms with exactly one defensible form. Anything needing a
choice — chance baseline, threshold, null model — is deferred to Phase 4/5. One stated
exception: a naive chance correction of the top-N metrics (the ``*_cc`` columns; see
topn_chance), stored so the results site can show it. It is a first pass; more
thorough corrections (a simulated null per (m, n), stratifying by n) stay deferred.
Every row
carries m (num_judges) and n (num_competitors) so later phases can normalise and
filter without re-reading the parsed files.

Phase 2 guarantees each scoresheet is valid: every judge's ranking is a full 1..n
permutation, num_judges >= 3, num_competitors >= 5. The metrics below assume that
(no ties, no partial lists).
"""

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PARSED_DIR = DATA_DIR / "parsed"
OUTPUT_PATH = DATA_DIR / "metrics.csv"

# ---------------------------------------------------------------------------
# Column ordering for the output CSV
# ---------------------------------------------------------------------------

# Parsed-file containers that are not scalar metadata (everything else is passed
# through). Excluding these leaves only the per-scoresheet scalar fields.
CONTAINER_FIELDS = {"judges", "competitors", "rankings"}

# Preferred metadata column order; any scalar field present but not listed here is
# appended (sorted) so new parsed-schema fields still appear without code changes.
PREFERRED_META_ORDER = [
    "id", "url", "raw_file", "site", "event_name", "event_id", "source_event_id",
    "event_start", "event_end", "event_date", "competition_name",
    "division_level", "dance_format", "num_judges", "num_competitors",
]

# Metric columns, grouped as in the implementation brief.
METRIC_COLS = [
    # Concordance
    "kendall_w", "mean_pairwise_rho",
    # Pairwise correlation / distance
    "mean_pairwise_tau", "tau_distance", "footrule_mean",
    # Pairwise distribution summaries (rogue-judge diagnostics)
    "min_pairwise_tau", "sd_pairwise_tau", "min_pairwise_rho", "sd_pairwise_rho",
    # Top-N set agreement
    "overlap_at_3", "overlap_at_5", "jaccard_at_3", "jaccard_at_5",
    # Top-N set agreement, naively chance-corrected (see topn_chance)
    "overlap_at_3_cc", "overlap_at_5_cc", "jaccard_at_3_cc", "jaccard_at_5_cc",
    # Rank dispersion
    "mean_abs_rank_dev_mean", "mean_abs_rank_dev_median", "sd_rank",
    # Rank dispersion divided by n/4 (see rank_dispersion)
    "mean_abs_rank_dev_mean_norm", "mean_abs_rank_dev_median_norm", "sd_rank_norm",
]


# ---------------------------------------------------------------------------
# Rank matrix
# ---------------------------------------------------------------------------

def build_matrix(doc: dict) -> np.ndarray:
    """Build the m x n integer rank matrix R from a parsed scoresheet.

    Rows are judges (in ``judges`` order), columns competitors (in ``competitors``
    order); R[j, i] is the rank judge j gave competitor i. R[:, i] is competitor i's
    m ranks; R[j] is judge j's ranking.
    """
    judges = doc["judges"]
    competitors = doc["competitors"]
    rankings = doc["rankings"]
    return np.array(
        [[rankings[j][c] for c in competitors] for j in judges],
        dtype=int,
    )


# ---------------------------------------------------------------------------
# Metric families (pure: matrix in -> scalar(s) out)
# ---------------------------------------------------------------------------

def kendall_w(R: np.ndarray) -> float:
    """Kendall's coefficient of concordance W = 12 S / [m^2 (n^3 - n)].

    S is the sum of squared deviations of competitor rank-sums about their mean
    R_bar = m(n+1)/2. Valid for tie-free full permutations (the Phase 2 guarantee).
    W in [0, 1], 1 = unanimity.
    """
    m, n = R.shape
    rank_sums = R.sum(axis=0)
    r_bar = m * (n + 1) / 2
    S = float(np.sum((rank_sums - r_bar) ** 2))
    return 12.0 * S / (m**2 * (n**3 - n))


def mean_pairwise_rho(R: np.ndarray) -> float:
    """Mean pairwise Spearman rho via the exact identity (mW - 1)/(m - 1).

    For tie-free rankings the mean of Spearman rho over all C(m,2) judge pairs equals
    this transform of W exactly (not just in expectation). Centred on 0 under chance
    for any m, so comparable across panel sizes — unlike raw W.
    """
    m = R.shape[0]
    W = kendall_w(R)
    return (m * W - 1.0) / (m - 1.0)


def pairwise_values(R: np.ndarray) -> dict[str, np.ndarray]:
    """Per-judge-pair tau, Spearman rho, and normalised footrule, in one pass.

    Returns arrays of length C(m,2). Footrule is the sum of absolute rank
    displacements divided by its exact maximum floor(n^2 / 2).
    """
    m, n = R.shape
    footrule_max = (n * n) // 2
    taus, rhos, footrules = [], [], []
    for a in range(m):
        ra = R[a]
        for b in range(a + 1, m):
            rb = R[b]
            tau, _ = kendalltau(ra, rb)
            rho, _ = spearmanr(ra, rb)
            taus.append(tau)
            rhos.append(rho)
            footrules.append(np.abs(ra - rb).sum() / footrule_max)
    return {
        "tau": np.array(taus, dtype=float),
        "rho": np.array(rhos, dtype=float),
        "footrule": np.array(footrules, dtype=float),
    }


def topn_overlap_jaccard(R: np.ndarray, N: int) -> tuple[float, float]:
    """Mean over judge pairs of top-N set overlap (|A∩B|/N) and Jaccard (|A∩B|/|A∪B|).

    Each judge's top-N set is the competitors they ranked 1..N. When N == n the
    top-N set is the whole field for every judge, so both measures are exactly 1.0
    (the degenerate whole-field case; n >= 5 is guaranteed, so only top-5 at n == 5
    ever hits this). Phase 5 filters on n if those rows are unwanted. The *_cc
    columns are NaN there (see topn_chance).
    """
    sets = [frozenset(np.flatnonzero(row <= N).tolist()) for row in R]
    m = len(sets)
    overlaps, jaccards = [], []
    for a in range(m):
        for b in range(a + 1, m):
            inter = len(sets[a] & sets[b])
            union = len(sets[a] | sets[b])
            overlaps.append(inter / N)
            jaccards.append(inter / union)
    return float(np.mean(overlaps)), float(np.mean(jaccards))


def topn_chance(n: int, N: int) -> tuple[float, float]:
    """Expected top-N overlap and Jaccard for one judge pair under chance.

    The null: each judge's top-N set is an independent, uniformly random N-subset
    of the n competitors. The intersection size i is then hypergeometric,
    P(i) = C(N,i) C(n-N,N-i) / C(n,N), so E[overlap] = E[i]/N = N/n and
    E[Jaccard] = sum_i P(i) i/(2N - i). A naive first-pass baseline: it ignores
    that real judges' top sets are correlated through the competitors' quality.
    """
    total = math.comb(n, N)
    e_jaccard = sum(math.comb(N, i) * math.comb(n - N, N - i) / total * i / (2 * N - i)
                    for i in range(max(0, 2 * N - n), N + 1))
    return N / n, e_jaccard


def chance_corrected(x: float, e: float) -> float:
    """(x - E)/(1 - E): 0 at chance, 1 for identical top-N sets; NaN when E == 1 (n == N)."""
    return (x - e) / (1.0 - e) if e < 1.0 else float("nan")


def rank_dispersion(R: np.ndarray) -> dict[str, float]:
    """Per-competitor spread of the m ranks it received, averaged over competitors.

    Three reductions of the same per-competitor spread, each raw (in places) and
    normalised (`*_norm`) so that finals of different sizes are roughly comparable:

    * The two MADs are divided by n/4: half the panel ranking in order and half
      in exact reverse gives every competitor a spread of |n + 1 - 2i|/2, which
      averages n/4 (even n; (n^2 - 1)/(4n) for odd n, slightly less for odd m).
      This is a construction, not a proven maximum: it held in an exhaustive
      search over small m, n and on the real data (max 0.98), and is proven for
      m = 2 only. Whether it's a true bound for the MADs is open.
    * The SD is divided by sqrt((n^2 - 1)/12), a proven upper bound: the mean
      within-competitor variance is (1 - W)(n^2 - 1)/12 <= (n^2 - 1)/12 and the
      mean of SDs is at most the root of the mean of variances (Jensen). It is
      attained (m = n judges in a cyclic Latin square, W = 0), but not for every
      panel size (for m = 2 the maximum is n/4). It's also the SD of ranks for
      one random judge, so ~1 is "as spread as a panel can be without agreeing".

    These are first-pass normalisations. They remove the main dependence on n, but not
    on m, and chance-level disagreement sits below 1 (about sqrt(1 - 1/m) for the
    SD). A rigorous correction (e.g. against the expectation under random
    rankings for the given m and n) is deferred; see plan.md.
    """
    n = R.shape[1]
    col_mean = R.mean(axis=0)
    col_median = np.median(R, axis=0)
    mad_mean = float(np.abs(R - col_mean).mean(axis=0).mean())
    mad_median = float(np.abs(R - col_median).mean(axis=0).mean())
    sd = float(R.std(axis=0, ddof=0).mean())
    return {
        "mean_abs_rank_dev_mean": mad_mean,
        "mean_abs_rank_dev_median": mad_median,
        "sd_rank": sd,
        "mean_abs_rank_dev_mean_norm": mad_mean / (n / 4.0),
        "mean_abs_rank_dev_median_norm": mad_median / (n / 4.0),
        "sd_rank_norm": sd / float(np.sqrt((n * n - 1) / 12.0)),
    }


def compute_metrics(doc: dict) -> dict[str, float]:
    """Compute the full panel of metric columns for one parsed scoresheet."""
    R = build_matrix(doc)
    m, n = R.shape
    W = kendall_w(R)
    pv = pairwise_values(R)
    tau, rho, footrule = pv["tau"], pv["rho"], pv["footrule"]
    mean_tau = float(tau.mean())
    overlap3, jaccard3 = topn_overlap_jaccard(R, 3)
    overlap5, jaccard5 = topn_overlap_jaccard(R, 5)
    e_o3, e_j3 = topn_chance(n, 3)
    e_o5, e_j5 = topn_chance(n, 5)

    return {
        "kendall_w": W,
        "mean_pairwise_rho": (m * W - 1.0) / (m - 1.0),
        "mean_pairwise_tau": mean_tau,
        "tau_distance": (1.0 - mean_tau) / 2.0,
        "footrule_mean": float(footrule.mean()),
        "min_pairwise_tau": float(tau.min()),
        "sd_pairwise_tau": float(tau.std(ddof=0)),
        "min_pairwise_rho": float(rho.min()),
        "sd_pairwise_rho": float(rho.std(ddof=0)),
        "overlap_at_3": overlap3,
        "overlap_at_5": overlap5,
        "jaccard_at_3": jaccard3,
        "jaccard_at_5": jaccard5,
        "overlap_at_3_cc": chance_corrected(overlap3, e_o3),
        "overlap_at_5_cc": chance_corrected(overlap5, e_o5),
        "jaccard_at_3_cc": chance_corrected(jaccard3, e_j3),
        "jaccard_at_5_cc": chance_corrected(jaccard5, e_j5),
        **rank_dispersion(R),
    }


# ---------------------------------------------------------------------------
# Row assembly / driver
# ---------------------------------------------------------------------------

def scalar_metadata(doc: dict) -> dict:
    """Pass-through metadata: every top-level scalar field of the parsed doc.

    Excludes the judges/competitors/rankings containers (and any other non-scalar),
    so the CSV is self-sufficient for Phase 4/5 joins without hardcoding the schema.
    """
    return {
        k: v for k, v in doc.items()
        if k not in CONTAINER_FIELDS and not isinstance(v, (list, dict))
    }


def ordered_columns(df: pd.DataFrame) -> list[str]:
    """Identifiers/metadata (preferred order, extras appended) then metric columns."""
    meta = [c for c in PREFERRED_META_ORDER if c in df.columns]
    extras = sorted(c for c in df.columns
                    if c not in PREFERRED_META_ORDER and c not in METRIC_COLS)
    metrics = [c for c in METRIC_COLS if c in df.columns]
    return meta + extras + metrics


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parsed-dir", type=Path, default=PARSED_DIR,
                    help="Directory of parsed {id}.json scoresheets.")
    ap.add_argument("--output", type=Path, default=OUTPUT_PATH,
                    help="Output CSV path (default: data/metrics.csv).")
    ap.add_argument("--limit", type=int, default=None,
                    help="Process only the first N files (debug).")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    files = sorted(args.parsed_dir.glob("*.json"))
    if args.limit is not None:
        files = files[: args.limit]
    if not files:
        raise SystemExit(f"No parsed files found in {args.parsed_dir}")

    records: list[dict] = []
    skips: list[tuple[str, str]] = []
    for path in tqdm(files, desc="metrics"):
        try:
            doc = json.loads(path.read_text())
            row = scalar_metadata(doc)
            row.update(compute_metrics(doc))
            records.append(row)
        except Exception as exc:  # Phase 2 should preclude this; log and skip.
            logging.warning("skipped %s: %s", path.name, exc)
            skips.append((path.name, str(exc)))

    df = pd.DataFrame(records)
    df = df[ordered_columns(df)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print(f"Wrote {args.output} — {len(df)} rows, {len(df.columns)} columns "
          f"({len(records)} processed, {len(skips)} skipped).")
    for name, err in skips:
        print(f"  skipped {name}: {err}")


if __name__ == "__main__":
    main()
