#!/usr/bin/env python3
"""Phase 2: Parse raw scoresheets into a standardised, validated JSON format.

Reads data/manifest.jsonl, runs each raw file through the vendored parser for its
site (scripts/parsers/), validates, normalises covariates, and writes one
data/parsed/{id}.json per scoresheet. Incremental and idempotent: a scoresheet
whose parsed file already exists is skipped.

See ~/.claude/plans/have-a-look-at-refactored-journal.md for the design rationale.
"""

import argparse
import html
import json
import logging
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from tqdm import tqdm

# Make the vendored `parsers` package importable when run as `python scripts/extract.py`.
sys.path.insert(0, str(Path(__file__).parent))
from parsers import detect_parser, detect_parser_by_content  # noqa: E402
from parsers import scoring_dance, eepro, danceconvention  # noqa: E402,F401 — registers parsers
from parsers.base import PrelimsError  # noqa: E402
from parsers.eepro import EeproParser  # noqa: E402
from parsers.danceconvention import DanceConventionParser  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "manifest.jsonl"
PARSED_DIR = DATA_DIR / "parsed"
INVENTORY_PATH = DATA_DIR / "division-inventory.html"
SKIPS_PATH = DATA_DIR / "extract-skips.html"


# ---------------------------------------------------------------------------
# Covariate normalisation
#
# NB: these keyword maps are a STARTING POINT grounded in a sample of the real
# data. The distinct division blobs must be eyeballed and the maps extended
# before the output is trusted — run inventory.py to review them.
# ---------------------------------------------------------------------------

# division_level is a single flat field: the skill ladder and the category/age
# divisions are peers (divisions in their own right, not orthogonal axes). When a
# category type co-occurs with a skill rung (rare, e.g. "Masters Novice"), the
# category wins — it is checked first. Patterns are tried top to bottom; first hit
# wins, so order encodes precedence.
LEVEL_PATTERNS: list[tuple[str, str]] = [
    # Category / age divisions (win over skill rungs — they are the division's
    # identity, e.g. "Masters Novice" → Masters). Pro-Am is NOT a level — it is
    # encoded in dance_format instead; level is the amateur's skill rung.
    ("Masters", r"\bmaster"),
    ("Sophisticated", r"\bsophisticated\b"),
    ("Junior", r"\bjunior|\byouth\b|\bteen\b"),
    ("Invitational", r"\binvitational\b|\binvite\b|\binvitation\b"),
    # Skill ladder, highest to lowest (combined rungs like "Advanced/All Star" or
    # "All-Stars/Champions" resolve to the higher one — matched first).
    ("Champions", r"\bchampion|\bchamps?\b"),
    ("All-Star", r"\ball[\s-]?stars?\b|\ballstar"),
    # All-American and its national variants: any "All <X>" blob not already caught
    # by All-Star above. \ball\b is intentionally broad — false positives (e.g.
    # "All Human") are acceptable.
    ("All-American", r"\ball\b"),
    ("Advanced", r"\badvanced?\b|\badv\b"),
    ("Intermediate", r"\bintermediate\b|\binterm\b|\binter\b(?!-)|\bint\b"),
    ("Novice", r"\bnovice\b|\bnov\b"),
    ("Newcomer", r"\bnewcomer\b|\bnew\b|\brookie\b|\bnewbie\b"),
    ("Open", r"\bopen\b"),
]

# Format detection regexes.
_PROAM_RE = re.compile(
    r"\bpro[\s./-]?am\b|\bam\s+(?:follow|fol|lead)\b",
    re.IGNORECASE,
)
# Role = the amateur's role.
_ROLE_LEADER_RE = re.compile(
    r"\(AmL\)|\bLEADERS?\b|\bL\s+final\b|\bam\s+lead",
    re.IGNORECASE,
)
_ROLE_FOLLOWER_RE = re.compile(
    r"\(AmF\)|\bFOLLOWERS?\b|\bF\s+final\b|\bam\s+(?:follow|fol)\b",
    re.IGNORECASE,
)
# Switchly/Switch/Role-Rotation detection precedes _STRICTLY_RE (switchly = Switch Strictly).
_SWITCH_RE = re.compile(r"\bswitch\b|\bswitchly\b|\brole[\s-]?rotation\b", re.IGNORECASE)
_RISING_STAR_RE = re.compile(r"\brising[\s-]?stars?\b", re.IGNORECASE)
# Strictly no longer includes switchly — that's handled by _SWITCH_RE above.
_STRICTLY_RE = re.compile(r"\bstrictly\b", re.IGNORECASE)
_JNJ_RE = re.compile(
    r"\bjack\s*[&'n]*\s*jill\b|\bjack\s+and\s+jill\b|\bjack[-\s]*n[-\s]*jill\b"
    r"|\bj\s*&\s*j\b|\bjnj\b|\bjandj\b",
    re.IGNORECASE,
)
# Classic, Showcase, and Cabaret are distinct formats — do not conflate them.
_CLASSIC_RE = re.compile(r"\bclassic\b", re.IGNORECASE)
_SHOWCASE_RE = re.compile(r"\bshowcase\b", re.IGNORECASE)
_ROUTINE_RE = re.compile(r"\broutines?\b", re.IGNORECASE)
# All-national pattern mirrors LEVEL_PATTERNS All-American entry; used to infer J&J format
# for All-X blobs (All-American, All-European, … are J&J by convention).
_ALL_NATIONAL_RE = re.compile(r"\ball\b", re.IGNORECASE)

# Abbreviation maps for div_token generation.
FORMAT_CODES: dict[str, str] = {
    "Jack & Jill": "jnj",
    "Strictly": "str",
    "Classic": "classic",
    "Routine": "routine",
    "Showcase": "showcase",
    "Rising Star": "risingstar",
    "Switch Jack & Jill": "swjnj",
    "Switch Strictly": "swstr",
    "Pro-Am Jack & Jill": "pamjnj",
    "Pro-Am Jack & Jill (Leader)": "pamljnj",
    "Pro-Am Jack & Jill (Follower)": "pamfjnj",
    "Pro-Am Strictly": "pamstr",
    "Pro-Am Strictly (Leader)": "pamlstr",
    "Pro-Am Strictly (Follower)": "pamfstr",
}

LEVEL_CODES: dict[str, str] = {
    "Newcomer": "new",
    "Novice": "nov",
    "Intermediate": "int",
    "Advanced": "adv",
    "All-Star": "als",
    "Champions": "chp",
    "Open": "opn",
    "Invitational": "inv",
    "All-American": "all",
    "Sophisticated": "sop",
    "Masters": "mas",
    "Junior": "jnr",
}

_FINALS_WORDS_RE = re.compile(r"\b(finals?|финал)\b", re.IGNORECASE)

# Matches dance styles that are definitively not WCS — mirrors the constant in download.py.
NON_WCS_STYLE_RE = re.compile(
    r"\b(?:salsa|bachata|zouk|lindy|hustle|country|silc|brazuka|ceroc|modern\s+jive|shag)",
    re.IGNORECASE,
)
# For raw-slug normalisation: shorten known format keywords even in fallback tokens.
_STRICTLY_NORM_RE = re.compile(r"\bstrictly(?:\s+swing)?\b", re.IGNORECASE)


def normalise_level(division_blob: str) -> str | None:
    """Return the division level, or None if no level is detectable."""
    low = division_blob.lower()
    for label, pat in LEVEL_PATTERNS:
        if re.search(pat, low):
            return label
    return None


def normalise_format(division_blob: str) -> str | None:
    """Return the dance format (including pro-am/switch variants), or None if undetectable.

    Detection priority (highest first):
      1. Pro-Am (existing logic)
      2. Switch/Switchly/Role Rotation → Switch J&J or Switch Strictly
      3. Rising Star (before Classic, which would otherwise catch "Routines")
      4. Strictly / J&J / Showcase / Classic / Routine
      5. All-national blobs (All-American etc.) → J&J by convention
    """
    # Pro-am: detect role then base dance.
    if _PROAM_RE.search(division_blob):
        if _ROLE_LEADER_RE.search(division_blob):
            role = " (Leader)"
        elif _ROLE_FOLLOWER_RE.search(division_blob):
            role = " (Follower)"
        else:
            role = ""
        if _STRICTLY_RE.search(division_blob):
            return f"Pro-Am Strictly{role}"
        if _JNJ_RE.search(division_blob):
            return f"Pro-Am Jack & Jill{role}"
        return f"Pro-Am Unknown{role}"

    # Switch / Switchly: "switchly" always means Switch Strictly.
    if _SWITCH_RE.search(division_blob):
        if re.search(r"\bswitchly\b", division_blob, re.IGNORECASE):
            return "Switch Strictly"
        if _JNJ_RE.search(division_blob):
            return "Switch Jack & Jill"
        if _STRICTLY_RE.search(division_blob):
            return "Switch Strictly"
        return None  # switch present but base dance unknown

    if _RISING_STAR_RE.search(division_blob):
        return "Rising Star"
    if _STRICTLY_RE.search(division_blob):
        return "Strictly"
    if _JNJ_RE.search(division_blob):
        return "Jack & Jill"
    if _SHOWCASE_RE.search(division_blob):
        return "Showcase"
    if _CLASSIC_RE.search(division_blob):
        return "Classic"
    if _ROUTINE_RE.search(division_blob):
        return "Routine"
    # All-national blobs (All-American, All-European, etc.) are Jack & Jill by convention.
    if _ALL_NATIONAL_RE.search(division_blob):
        return "Jack & Jill"
    return None


def make_div_token_base(blob: str, level: str | None, fmt: str | None) -> str:
    """Compute the div_token (format_code + level_code, or raw slug fallback).

    Both format and level must be in their respective code maps to get an
    abbreviated token; otherwise falls back to a slug of the blob minus round words.
    """
    fmt_code = FORMAT_CODES.get(fmt) if fmt is not None else None
    level_code = LEVEL_CODES.get(level) if level is not None else None
    if fmt_code is not None and level_code is not None:
        return f"{fmt_code}_{level_code}"
    if fmt_code is not None:
        return fmt_code
    # Raw fallback: strip round words, then shorten known format keywords.
    s = _FINALS_WORDS_RE.sub(" ", blob)
    s = _JNJ_RE.sub("jnj", s)
    s = _STRICTLY_NORM_RE.sub("str", s)
    return slugify(s) or slugify(blob)


# ---------------------------------------------------------------------------
# Division-blob isolation (per-site; see plan)
# ---------------------------------------------------------------------------

def _norm_ws(s: str) -> str:
    return " ".join(s.split())


def isolate_division_blob(
    site: str, competition_name: str, event_name: str, eepro_division: str | None
) -> str:
    """Return the division/round text, stripped of the event name where possible.

    The division's position inside competition_name differs by site, and event
    names can contain level words, so we isolate the division text before keyword
    matching. competition_name is kept verbatim elsewhere for audit.
    """
    if site == "eepro.com" and eepro_division is not None:
        return eepro_division

    comp = competition_name
    if site == "scoring.dance":
        # competition_name = "{event} - {round_name}"; round_name is the last segment.
        return comp.rsplit(" - ", 1)[-1].strip() if " - " in comp else comp.strip()

    if site == "danceconvention.net":
        # competition_name = "{division} - [round -] {event}"; remove the event name.
        # The manifest event_name may carry raw HTML entities (e.g. "Swing&amp;Snow")
        # while the parser's competition_name is already unescaped — compare unescaped.
        ev = _norm_ws(html.unescape(event_name))
        comp_n = _norm_ws(comp)
        if ev and ev in comp_n:
            comp_n = comp_n.replace(ev, " ")
        return comp_n.strip(" -").strip() or comp.strip()

    return comp.strip()


# ---------------------------------------------------------------------------
# Other field derivations
# ---------------------------------------------------------------------------

def canonical_event_date(event_start: date, event_end: date) -> date:
    """The Saturday within [start, end] if one exists, else event_start."""
    if event_end < event_start:
        event_start, event_end = event_end, event_start
    day = event_start
    while day <= event_end:
        if day.weekday() == 5:  # Saturday
            return day
        day += timedelta(days=1)
    return event_start


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def make_id(event_id: str, event_slug: str, div_token: str, used: set[str]) -> str:
    """Build a unique scoresheet id, appending a numeric suffix on intra-event collision.

    Format: `{event_id}_{event_slug}_{div_token}` e.g. `sd-228_swingcouver-2025_str_chp`.
    `event_id` carries global uniqueness; `event_slug` is decorative (kebab-case);
    `div_token` is the output of make_div_token_base().

    Disambiguation is against the ids already assigned THIS run only — never disk
    state. Because the manifest is processed in a stable (append-only) order, a
    given scoresheet lands on the same id every run, which is what makes the
    out_path.exists() cache check (and thus idempotency) correct. Collisions are
    strictly intra-event (same event_id + same div_token), which the --site/--start/
    --end/--event filters can never split, so the positional suffix stays stable.
    """
    base = "_".join(p for p in (event_id, event_slug, div_token) if p)
    base = base or "scoresheet"
    candidate = base
    n = 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


# ---------------------------------------------------------------------------
# Validation (skip on incomplete/too-small data or integrity anomalies)
# ---------------------------------------------------------------------------

class IntegrityError(Exception):
    """A parsed scoresheet is internally inconsistent.

    May indicate a parser bug, but can also arise from genuinely unsupported
    source data (e.g. duplicate ranks from judge error). The main loop catches
    these and adds them to the skip list rather than aborting the run.
    """


def block_structure(values: list[int], n: int) -> int | None:
    """Classify a judge's placement multiset over n competitors.

    Returns:
        1     if `values` is a clean permutation of 1..n (a normal ranking),
        k>1   if `values` is exactly k identical blocks of 1..(n/k) — the shape
              produced by a role-separated sheet (e.g. leaders + followers each
              ranked 1..m in one table),
        None  if it is neither (an unexplained corruption).
    """
    counts = Counter(values)
    k = counts.get(1, 0)
    if k == 0 or n % k != 0:
        return None
    m = n // k
    if counts == Counter({r: k for r in range(1, m + 1)}):
        return k
    return None


# Non-finals round markers, as a content-level safety net. Phase 1 filters most
# prelims at discovery and the parsers raise PrelimsError for callback rounds, but
# numeric prelims (e.g. eepro "All American Prelims", an 82-couple relative-
# placement field) can leak through — they carry the round word in their name.
# Match on word roots with a leading boundary only — the source text can run the
# round word into the next word (e.g. "PrelimsAll ties broken…"), so a trailing
# boundary would miss it. `\bsemis?\b`/`\bsemi-?final` avoid matching "seminar".
NON_FINALS_RE = re.compile(
    r"\bprelim|\bquarter|\bqualif|\bcallback|\bheats?\b|\bround\s*\d|"
    r"\bsemis?\b|\bsemi-?final|отбор|полуфинал|четвертьфинал",
    re.IGNORECASE,
)


def looks_like_non_finals(competition_name: str) -> bool:
    return bool(NON_FINALS_RE.search(competition_name))


def validate(scoresheet) -> str | None:
    """Validate a parsed scoresheet.

    Returns None if OK, or a skip reason string for data we should drop. Raises
    IntegrityError for violations that signal a parser bug (e.g. mismatched
    judge keys, unexplained non-permutation values); the caller catches these.
    """
    judges = scoresheet.judges
    competitors = scoresheet.competitors
    n = len(competitors)

    # Size floor → skip (legitimately odd source data, not a bug).
    if len(judges) < 3:
        return f"too few judges ({len(judges)})"
    if n < 5:
        return f"too few competitors ({n})"

    # rankings keys must match the judges list exactly → integrity (parser bug).
    if set(scoresheet.rankings.keys()) != set(judges):
        raise IntegrityError(
            f"rankings keys {sorted(scoresheet.rankings)} != judges {sorted(judges)}"
        )

    blocks_per_judge = []  # k for each judge: 1 = clean permutation, >1 = multi-block
    for judge in judges:
        row = scoresheet.rankings[judge]
        # Missing competitor or a 0 placeholder → incomplete source data → skip.
        if any(c not in row for c in competitors):
            return f"judge {judge!r} missing a competitor placement"
        values = [row[c] for c in competitors]
        if any(v == 0 for v in values):
            return f"judge {judge!r} has an unparsed (0) placement"
        k = block_structure(values, n)
        if k is None:
            # Genuine values present but neither a permutation nor a clean set of
            # equal blocks → unexplained, signals a parser bug.
            if min(values) >= 70 and max(values) <= 100:
                return "raw scores out of 100 (not placements)"
            raise IntegrityError(
                f"judge {judge!r} ranking is not a permutation of 1..{n}: {sorted(values)}"
            )
        blocks_per_judge.append(k)

    # Role-separated divisions (e.g. leaders and followers each ranked 1..m on one
    # sheet) come through as k>1 blocks for EVERY judge. They aren't a single panel
    # ranking, so we skip them. Inconsistent blocking across judges is suspicious →
    # let it crash as an integrity issue.
    if all(k == 1 for k in blocks_per_judge):
        return None
    if len(set(blocks_per_judge)) == 1:
        return f"role-separated / multi-block ranking ({blocks_per_judge[0]} blocks)"
    raise IntegrityError(
        f"inconsistent ranking block structure across judges: {blocks_per_judge}"
    )


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def load_manifest() -> list[dict]:
    records = []
    for line in MANIFEST_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# Short `--site` names → the values stored in the manifest.
SITE_ALIASES = {
    "scoring.dance": "scoring.dance",
    "eepro": "eepro.com",
    "danceconvention": "danceconvention.net",
}


def select_records(
    records: list[dict],
    sites: set[str] | None,
    start: date | None,
    end: date | None,
    event: str | None,
) -> list[dict]:
    """Filter manifest records by site, event date-range overlap, and event name.

    A record matches the date window if its [event_start, event_end] overlaps
    [start, end] (either bound may be open). `event` is a case-insensitive
    substring match on event_name. Order is preserved so collision suffixes stay
    stable (colliding pairs share an event, so they are never split by a filter).
    """
    out = []
    for r in records:
        if sites is not None and r["site"] not in sites:
            continue
        if start is not None and date.fromisoformat(r["event_end"]) < start:
            continue
        if end is not None and date.fromisoformat(r["event_start"]) > end:
            continue
        if event is not None and event.lower() not in r["event_name"].lower():
            continue
        out.append(r)
    return out


# ---------------------------------------------------------------------------
# Per-scoresheet extraction
# ---------------------------------------------------------------------------

def parse_targets(record: dict, content: bytes) -> list[str | None]:
    """Return the list of `division` arguments to parse for this manifest entry.

    eepro pages are 1:M (one file per division); danceconvention PDFs are
    usually 1:1 but pro-am sheets contain two competitions (leaders + followers).
    """
    if record["site"] == "eepro.com":
        names = EeproParser().get_division_names(content)
        return list(names)  # may be empty (e.g. prelims-only page)
    if record["site"] == "danceconvention.net":
        names = DanceConventionParser().get_division_names(content)
        return list(names)
    return [None]


def _reason_key(r: str) -> str:
    """Normalise a skip reason to a summary bucket label.

    Strips quoted identifiers (e.g. judge names) so per-name variants group
    together, truncates at the first ': ' to drop long error details, then
    removes a trailing parenthetical (e.g. '(3)', '(name)') that only adds
    noise to the summary.
    """
    r = re.sub(r"'[^']*'", "...", r)           # remove quoted names
    r = re.split(r": ", r, 1)[0]               # drop long detail after ': '
    r = re.sub(r"\s+\([^)]*\)\s*$", "", r)     # strip trailing (...)
    return r.strip()


_SKIPS_CSS = """\
    body { font-family: system-ui, sans-serif; font-size: 14px; padding: 1em 2em; color: #222; }
    h1 { font-size: 1.2em; margin-bottom: .25em; }
    h2 { font-size: 1.0em; margin: 1.2em 0 .3em; }
    p.stats { color: #555; margin-top: 0; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 1.5em; }
    th, td { text-align: left; padding: 4px 10px; border: 1px solid #ddd; }
    thead th { background: #444; color: #fff; }
    tbody tr:nth-child(even) { background: #f9f9f9; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; color: #555; }
    a { color: #1d4ed8; word-break: break-all; }
"""


def write_skips_html(skips: list[tuple[str, str | None, str, str]], output_path: Path) -> None:
    """Write an HTML skip report to output_path."""
    def _e(s: object) -> str:
        return html.escape(str(s))

    n = len(skips)
    reason_counts = Counter(_reason_key(r) for _, _, r, _ in skips)

    summary_rows = "".join(
        f'<tr><td class="num">{count}</td><td>{_e(reason)}</td></tr>\n'
        for reason, count in reason_counts.most_common()
    )

    detail_rows = "".join(
        f'<tr>'
        f'<td>{_e(event_name)}</td>'
        f'<td>{_e(division) if division else ""}</td>'
        f'<td>{_e(reason)}</td>'
        f'<td><a href="{_e(url)}" target="_blank" rel="noopener">{_e(url)}</a></td>'
        f'</tr>\n'
        for event_name, division, reason, url in skips
    )

    page = (
        f'<!DOCTYPE html>\n'
        f'<html lang="en">\n'
        f'<head>\n'
        f'<meta charset="utf-8">\n'
        f'<title>Extract Skips</title>\n'
        f'<style>\n{_SKIPS_CSS}</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<h1>Extract Skips</h1>\n'
        f'<p class="stats">{n} total skips</p>\n'
        f'<h2>Reason summary</h2>\n'
        f'<table>\n'
        f'<thead><tr><th>Count</th><th>Reason</th></tr></thead>\n'
        f'<tbody>\n{summary_rows}</tbody>\n'
        f'</table>\n'
        f'<h2>Detail</h2>\n'
        f'<table>\n'
        f'<thead><tr><th>Event</th><th>Division</th><th>Reason</th><th>URL</th></tr></thead>\n'
        f'<tbody>\n{detail_rows}</tbody>\n'
        f'</table>\n'
        f'</body>\n'
        f'</html>\n'
    )
    output_path.write_text(page, encoding="utf-8")
    print(f"Wrote {output_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-inventory",
        action="store_true",
        help="Skip writing data/division_inventory.html after extraction.",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Re-extract and overwrite parsed files that already exist (default: "
             "skip already-parsed scoresheets).",
    )
    ap.add_argument(
        "--site",
        choices=list(SITE_ALIASES),
        action="append",
        dest="sites",
        help="Only process this site (repeatable; default: all).",
    )
    ap.add_argument("--start", type=date.fromisoformat, default=None,
                    help="Only events ending on/after this date (YYYY-MM-DD).")
    ap.add_argument("--end", type=date.fromisoformat, default=None,
                    help="Only events starting on/before this date (YYYY-MM-DD).")
    ap.add_argument("--event", default=None,
                    help="Only events whose name contains this text (case-insensitive).")
    ap.add_argument("--limit", type=int, default=None, help="Process only the first N (post-filter) entries (debug).")
    args = ap.parse_args()

    all_records = load_manifest()
    sites = {SITE_ALIASES[s] for s in args.sites} if args.sites else None
    records = select_records(all_records, sites, args.start, args.end, args.event)
    logging.info(f"Selected {len(records)} of the manifest's entries to process.")
    if args.limit:
        records = records[: args.limit]

    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    used_ids: set[str] = set()
    skips: list[tuple[str, str | None, str, str]] = []  # (event_name, division, reason, url)
    written = 0
    division_audit: list[tuple[str, str, str, str, str]] = []  # (site, blob, level, fmt, url)

    for record in tqdm(records, unit="sheet"):
        url = record["url"]
        site = record["site"]
        event_name = record["event_name"]
        event_start = date.fromisoformat(record["event_start"])
        event_end = date.fromisoformat(record["event_end"])
        local_path = Path(record["local_path"])

        if NON_WCS_STYLE_RE.search(event_name):
            skips.append((event_name, None, "non-WCS event (name)", url))
            continue

        if not local_path.exists():
            skips.append((event_name, None, f"raw file missing: {local_path}", url))
            continue

        content = local_path.read_bytes()
        parser = detect_parser(url) or detect_parser_by_content(content, url)
        if parser is None:
            skips.append((event_name, None, "no parser matched", url))
            continue

        try:
            divisions = parse_targets(record, content)
        except Exception as e:
            skips.append((event_name, None, f"division enumeration failed: {e}", url))
            continue
        if not divisions:
            skips.append((event_name, None, "no finals divisions found", url))
            continue

        for div_arg in divisions:
            try:
                scoresheet = parser.parse(url, content, division=div_arg)
            except PrelimsError:
                skips.append((event_name, div_arg, "prelims/callback round", url))
                continue
            except Exception as e:
                skips.append((event_name, div_arg, f"parse error: {type(e).__name__}: {e}", url))
                continue

            division_blob = isolate_division_blob(
                site, scoresheet.competition_name, event_name, div_arg
            )

            # Content-level non-finals safety net (numeric prelims that the
            # parser's callback check and the Phase 1 URL filter both missed).
            if looks_like_non_finals(scoresheet.competition_name):
                skips.append((event_name, division_blob, "non-finals round (name)", url))
                continue

            # Validation: integrity violations are caught and logged as skips.
            # Both modes treat them gracefully — they may indicate a parser bug
            # or duplicate placements from judge error; neither aborts the run.
            try:
                reason = validate(scoresheet)
            except IntegrityError as e:
                skips.append((event_name, division_blob, f"integrity error: {e}", url))
                continue
            if reason is not None:
                skips.append((event_name, division_blob, reason, url))
                continue

            level = normalise_level(division_blob)
            fmt = normalise_format(division_blob)
            if NON_WCS_STYLE_RE.search(division_blob):
                skips.append((event_name, division_blob, "non-WCS dance style", url))
                continue
            division_audit.append((site, division_blob, level, fmt, url))

            div_token = make_div_token_base(division_blob, level, fmt)
            event_slug = slugify(event_name).replace("_", "-")
            entry_id = make_id(record["event_id"], event_slug, div_token, used_ids)
            out_path = PARSED_DIR / f"{entry_id}.json"
            if out_path.exists() and not args.force:
                continue

            doc = {
                "id": entry_id,
                "url": url,
                "raw_file": local_path.name,  # basename within data/raw/ (eepro: 1 file → many divisions)
                "site": site,
                "event_name": event_name,
                "event_id": record["event_id"],
                "source_event_id": record["source_event_id"],
                "event_start": record["event_start"],
                "event_end": record["event_end"],
                "event_date": canonical_event_date(event_start, event_end).isoformat(),
                "competition_name": scoresheet.competition_name,
                "division_level": level,
                "dance_format": fmt,
                "num_judges": scoresheet.num_judges,
                "num_competitors": scoresheet.num_competitors,
                "judges": scoresheet.judges,
                "competitors": scoresheet.competitors,
                "rankings": scoresheet.rankings,
            }
            out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
            written += 1
            logging.debug(f"wrote {entry_id}  ({level} / {fmt}, J={doc['num_judges']} C={doc['num_competitors']})")

    # ---- summaries ----
    logging.info(f"Done. Wrote {written} parsed files; skipped {len(skips)}.")
    if skips:
        reason_counts = Counter(_reason_key(r) for _, _, r, _ in skips)
        print("\n=== Skip summary ===")
        for reason, count in reason_counts.most_common():
            print(f"  {count:4d}  {reason}")
        write_skips_html(skips, SKIPS_PATH)
    if not args.no_inventory:
        from inventory import write_inventory
        write_inventory(division_audit, INVENTORY_PATH)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
