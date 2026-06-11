#!/usr/bin/env python3
"""Generate data/division_inventory.html — a browsable audit of division classifications.

Run standalone to regenerate the inventory without writing parsed files:

    python scripts/inventory.py [--site ...] [--start DATE] [--end DATE]
"""

import html
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

_SITE_ABBREV = {"scoring.dance": "sd", "eepro.com": "ee", "danceconvention.net": "dc"}

DATA_DIR = Path(__file__).parent.parent / "data"
INVENTORY_PATH = DATA_DIR / "division_inventory.html"

_CSS = """\
    body { font-family: system-ui, sans-serif; font-size: 14px; padding: 1em 2em; color: #222; }
    h1 { font-size: 1.2em; margin-bottom: .25em; }
    p.stats { color: #555; margin-top: 0; }
    table { border-collapse: collapse; width: 100%; }
    th, td { text-align: left; padding: 4px 10px; border: 1px solid #ddd; }
    thead th { background: #444; color: #fff; }
    tbody tr:nth-child(even) { background: #f9f9f9; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; color: #555; }
    code { background: #eee; padding: 1px 5px; border-radius: 3px; font-size: .9em; }
    .flag-nolevel { color: #b45309; }
    .flag-unclassified { color: #b91c1c; font-weight: bold; }
    details { margin: 0; }
    summary { cursor: pointer; }
    .blob-table { margin: 4px 0 4px 1em; background: #f0f4f8; }
    .blob-table td { border-color: #c5d5e8; font-size: .9em; }
"""


def _e(s: object) -> str:
    return html.escape(str(s))


def _site_str(sites_counter: Counter) -> str:
    return "+".join(
        f"{_SITE_ABBREV.get(s, s)}:{c}"
        for s, c in sorted(sites_counter.items())
    )


def write_inventory(audit: list[tuple[str, str, str, str]], output_path: Path) -> None:
    """Write an HTML division inventory to output_path."""
    from extract import FORMAT_CODES, LEVEL_CODES, make_div_token_base  # lazy to avoid circular import
    by_token: dict[str, dict] = {}
    for site, blob, level, fmt in audit:
        token = make_div_token_base(blob, level, fmt)
        if token not in by_token:
            by_token[token] = {"level": level, "fmt": fmt, "count": 0, "sites": Counter(), "blobs": {}}
        by_token[token]["count"] += 1
        by_token[token]["sites"][site] += 1
        if blob not in by_token[token]["blobs"]:
            by_token[token]["blobs"][blob] = Counter()
        by_token[token]["blobs"][blob][site] += 1

    n_blobs = sum(len(g["blobs"]) for g in by_token.values())
    sorted_tokens = sorted(by_token.items(), key=lambda x: -x[1]["count"])

    rows = []
    for token, info in sorted_tokens:
        level = info["level"]
        fmt = info["fmt"]
        fmt_code = FORMAT_CODES.get(fmt) if fmt is not None else None
        level_code = LEVEL_CODES.get(level) if level is not None else None

        if fmt_code is not None and level_code is not None:
            flag_html = ""
        elif fmt_code is not None:
            flag_html = ' <span class="flag-nolevel">(no level)</span>'
        else:
            flag_html = ' <span class="flag-unclassified">UNCLASSIFIED</span>'

        sorted_blobs = sorted(info["blobs"].items(), key=lambda x: -sum(x[1].values()))
        n_in_group = len(info["blobs"])

        blob_rows = "".join(
            f'<tr>'
            f'<td class="num">{sum(bs.values())}</td>'
            f'<td>{_e(_site_str(bs))}</td>'
            f'<td>{_e(blob)}</td>'
            f'</tr>'
            for blob, bs in sorted_blobs
        )
        blob_cell = (
            f'<details><summary>{n_in_group} blob(s){flag_html}</summary>'
            f'<table class="blob-table">{blob_rows}</table></details>'
        )

        rows.append(
            f'<tr>'
            f'<td class="num">{info["count"]}</td>'
            f'<td>{_e(_site_str(info["sites"]))}</td>'
            f'<td>{_e(level or "—")}</td>'
            f'<td>{_e(fmt or "—")}</td>'
            f'<td><code>{_e(token)}</code></td>'
            f'<td>{blob_cell}</td>'
            f'</tr>\n'
        )

    page = (
        f'<!DOCTYPE html>\n'
        f'<html lang="en">\n'
        f'<head>\n'
        f'<meta charset="utf-8">\n'
        f'<title>Division Inventory</title>\n'
        f'<style>\n{_CSS}</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<h1>Division Inventory</h1>\n'
        f'<p class="stats">'
        f'{n_blobs} distinct division blobs &bull; '
        f'{len(by_token)} classifications &bull; '
        f'{len(audit)} total scoresheets'
        f'</p>\n'
        f'<table>\n'
        f'<thead><tr>'
        f'<th>Freq</th><th>Sites</th><th>Level</th><th>Format</th>'
        f'<th>div_token</th><th>Blobs</th>'
        f'</tr></thead>\n'
        f'<tbody>\n'
        f'{"".join(rows)}'
        f'</tbody>\n'
        f'</table>\n'
        f'</body>\n'
        f'</html>\n'
    )
    output_path.write_text(page, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    import argparse
    import logging
    from datetime import date as _date

    from parsers.base import PrelimsError
    from extract import (
        IntegrityError, NON_WCS_STYLE_RE, SITE_ALIASES,
        detect_parser, detect_parser_by_content,
        isolate_division_blob, load_manifest, looks_like_non_finals,
        normalise_format, normalise_level, parse_targets,
        select_records, validate,
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", choices=list(SITE_ALIASES), action="append", dest="sites",
                    help="Restrict to this site (repeatable).")
    ap.add_argument("--start", type=_date.fromisoformat, default=None,
                    help="Only events ending on/after this date (YYYY-MM-DD).")
    ap.add_argument("--end", type=_date.fromisoformat, default=None,
                    help="Only events starting on/before this date (YYYY-MM-DD).")
    ap.add_argument("--event", default=None,
                    help="Only events whose name contains this text (case-insensitive).")
    ap.add_argument("--limit", type=int, default=None, help="Process only the first N entries.")
    ap.add_argument("--output", type=Path, default=INVENTORY_PATH,
                    help=f"Output path (default: {INVENTORY_PATH}).")
    args = ap.parse_args()

    all_records = load_manifest()
    sites = {SITE_ALIASES[s] for s in args.sites} if args.sites else None
    records = select_records(all_records, sites, args.start, args.end, args.event)
    if args.limit:
        records = records[: args.limit]

    div_audit: list[tuple[str, str, str, str]] = []
    total = len(records)
    _last_progress = 0.0

    for rec_idx, record in enumerate(records):
        _now = time.monotonic()
        if _now - _last_progress >= 3.0:
            print(f"  [{rec_idx}/{total}]", flush=True)
            _last_progress = _now

        url = record["url"]
        site = record["site"]
        event_name = record["event_name"]
        local_path = Path(record["local_path"])

        if NON_WCS_STYLE_RE.search(event_name):
            continue
        if not local_path.exists():
            continue
        content = local_path.read_bytes()
        parser = detect_parser(url) or detect_parser_by_content(content, url)
        if parser is None:
            continue
        try:
            divisions = parse_targets(record, content)
        except Exception:
            continue
        if not divisions:
            continue

        for div_arg in divisions:
            try:
                scoresheet = parser.parse(url, content, division=div_arg)
            except PrelimsError:
                continue
            except Exception:
                continue
            if looks_like_non_finals(scoresheet.competition_name):
                continue
            try:
                reason = validate(scoresheet)
            except IntegrityError:
                continue
            if reason is not None:
                continue
            blob = isolate_division_blob(site, scoresheet.competition_name, event_name, div_arg)
            level = normalise_level(blob)
            fmt = normalise_format(blob)
            if NON_WCS_STYLE_RE.search(blob):
                continue
            div_audit.append((site, blob, level, fmt))

    write_inventory(div_audit, args.output)
