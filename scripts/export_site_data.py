#!/usr/bin/env python3
"""Export the in-scope scoresheets as JSON for the results site (site/).

Reads data/metrics.csv (Phase 3), data/parsed/{id}.json (Phase 2) and
lookups/regions.json (Task 4A) and writes, in site/src/lib/data/:

  sheets.json   one entry per in-scope scoresheet: metadata, source URL, judge
                and competitor names, the judge x competitor rank matrix R, and
                compute_metrics.py's value of every metric (``py``), so the site
                can recompute each metric in JS and check it against Python.
  export.json   snapshot info: when and from which commit this was exported,
                the event-date range and the row counts.

In scope: Jack & Jill and Strictly finals at the six main levels — the same
filter as notebooks/explore_metrics.ipynb.

The output is committed: CI builds the site from it without rerunning the
pipeline (data/ is gitignored).
"""

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from compute_metrics import build_matrix

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PARSED_DIR = DATA_DIR / "parsed"
REGIONS_PATH = PROJECT_ROOT / "lookups" / "regions.json"
OUT_DIR = PROJECT_ROOT / "site" / "src" / "lib" / "data"

FORMATS = {"Jack & Jill": "jnj", "Strictly": "strictly"}
LEVELS = {
    "Newcomer": "new", "Novice": "nov", "Intermediate": "int",
    "Advanced": "adv", "All-Star": "als", "Champions": "chp",
}
# The metrics shown on the site. This started as the notebook's METRICS list; the site
# has since dropped the top-5 metrics (degenerate in finals of 5, which are common at
# the upper levels) and added the naively chance-corrected top-3 metrics, which the
# notebook doesn't show.
METRICS = [
    "kendall_w", "mean_pairwise_rho", "mean_pairwise_tau", "tau_distance", "footrule_mean",
    "overlap_at_3_cc", "jaccard_at_3_cc", "overlap_at_3", "jaccard_at_3",
    "mean_abs_rank_dev_mean", "mean_abs_rank_dev_median", "sd_rank",
]


def git_commit() -> str:
    """Short HEAD commit, with "-dirty" if the working tree has tracked changes."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    sha = git("rev-parse", "--short", "HEAD")
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", "scripts")
    return sha + ("-dirty" if dirty else "")


def main() -> None:
    df = pd.read_csv(DATA_DIR / "metrics.csv")
    df = df[df["dance_format"].isin(FORMATS) & df["division_level"].isin(LEVELS)]
    df = df.sort_values(["event_date", "event_name", "competition_name", "id"])

    regions = json.loads(REGIONS_PATH.read_text())

    sheets = []
    for row in df.itertuples(index=False):
        doc = json.loads((PARSED_DIR / f"{row.id}.json").read_text())
        R = build_matrix(doc)
        region = regions.get(doc["event_id"], {})
        sheets.append({
            "id": row.id,
            "format": FORMATS[row.dance_format],
            "level": LEVELS[row.division_level],
            "event": row.event_name,
            "date": row.event_date,
            "name": row.competition_name,
            "country": region.get("country"),  # ISO 3166-1 alpha-2, e.g. "DE"
            "state": region.get("state"),      # ISO 3166-2, US only, e.g. "US-CA"
            "site": row.site,
            "url": row.url,
            "judges": doc["judges"],
            "competitors": doc["competitors"],
            "R": R.tolist(),
            "py": {m: float(getattr(row, m)) for m in METRICS},
        })
        bad = [m for m, v in sheets[-1]["py"].items() if not math.isfinite(v)]
        if bad:  # JSON has no NaN, and the site assumes every exported value is finite.
            raise SystemExit(f"{row.id}: non-finite {', '.join(bad)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sheets.json").write_text(json.dumps(sheets, ensure_ascii=False, separators=(",", ":")))

    counts = df.groupby(["dance_format", "division_level"]).size()
    info = {
        "exported": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "commit": git_commit(),
        "first_event": df["event_date"].min(),
        "last_event": df["event_date"].max(),
        "sheets": len(sheets),
        "counts": {FORMATS[f]: {LEVELS[l]: int(n) for (ff, l), n in counts.items() if ff == f}
                   for f in FORMATS},
    }
    (OUT_DIR / "export.json").write_text(json.dumps(info, indent=1) + "\n")
    print(f"Wrote {len(sheets)} sheets to {OUT_DIR / 'sheets.json'}")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
