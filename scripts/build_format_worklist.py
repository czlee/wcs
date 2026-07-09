#!/usr/bin/env python3
"""Build the competition-format labeling worklist for Task 4B (see plan.md).

Reads ``data/metrics.csv`` and emits one row per final to be labeled with its floor
format (all-skate / cluster / spotlight). The pilot is scoped to Intermediate-level
J&J/Strictly finals from 2025 (see plan.md Task 4B).

The output (``lookups/formats.csv``) is a *human-edited* artifact: Claude pre-fills the
context columns and candidate source links, the user fills the label columns. Re-running
this script is therefore safe — labeler-entered values for ids already present are
preserved (merged), and rows are only ever added, never silently overwritten.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Columns carried over from metrics.csv as read-only context for the labeler.
CONTEXT_COLS = [
    "id",
    "event_id",
    "event_name",
    "event_date",
    "competition_name",
    "dance_format",
    "num_competitors",
    "site",
    "url",
]
# Columns the labeler (and Claude's prep pass) fill in. Preserved across re-runs.
LABEL_COLS = ["format", "source_url", "source_type", "confidence", "source_pass", "notes"]

ALL_COLS = CONTEXT_COLS + LABEL_COLS


def load_existing_labels(out_path: Path) -> dict[str, dict[str, str]]:
    """Return {id: {label_col: value}} for any already-filled label cells."""
    if not out_path.exists():
        return {}
    preserved: dict[str, dict[str, str]] = {}
    with out_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            filled = {c: row[c] for c in LABEL_COLS if row.get(c, "").strip()}
            if filled:
                preserved[row["id"]] = filled
    return preserved


def build(metrics_path: Path, out_path: Path, level: str, year: str,
          formats: set[str]) -> None:
    preserved = load_existing_labels(out_path)

    rows: list[dict[str, str]] = []
    with metrics_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("division_level") != level:
                continue
            if r.get("dance_format") not in formats:
                continue
            if (r.get("event_date") or "")[:4] != year:
                continue
            row = {c: r.get(c, "") for c in CONTEXT_COLS}
            for c in LABEL_COLS:
                row[c] = ""
            row.update(preserved.get(r["id"], {}))  # carry over any prior labels
            rows.append(row)

    # Group by event, then chronological, then format — so the labeler can fill an
    # event's finals together (often a uniform per-event policy).
    rows.sort(key=lambda x: (x["event_name"], x["event_date"], x["dance_format"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALL_COLS)
        w.writeheader()
        w.writerows(rows)

    n_events = len({r["event_id"] for r in rows})
    by_fmt: dict[str, int] = {}
    n_preserved = 0
    for r in rows:
        by_fmt[r["dance_format"]] = by_fmt.get(r["dance_format"], 0) + 1
        if r["id"] in preserved:
            n_preserved += 1
    print(f"Wrote {len(rows)} finals across {n_events} events -> {out_path}")
    print(f"  filter: level={level!r} year={year} formats={sorted(formats)}")
    print(f"  by dance_format: {by_fmt}")
    if preserved:
        print(f"  preserved prior labels on {n_preserved} row(s)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metrics", type=Path, default=REPO_ROOT / "data" / "metrics.csv")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "lookups" / "formats.csv")
    p.add_argument("--level", default="Intermediate")
    p.add_argument("--year", default="2025")
    p.add_argument("--formats", default="Jack & Jill,Strictly",
                   help="comma-separated dance_format values to include")
    args = p.parse_args()
    formats = {s.strip() for s in args.formats.split(",") if s.strip()}
    build(args.metrics, args.out, args.level, args.year, formats)


if __name__ == "__main__":
    main()
