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

# Make the vendored `parsers` package importable when run as `python scripts/extract.py`.
sys.path.insert(0, str(Path(__file__).parent))
from parsers import detect_parser, detect_parser_by_content  # noqa: E402
from parsers import scoring_dance, eepro, danceconvention  # noqa: E402,F401 — registers parsers
from parsers.base import PrelimsError  # noqa: E402
from parsers.eepro import EeproParser  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "manifest.jsonl"
PARSED_DIR = DATA_DIR / "parsed"


# ---------------------------------------------------------------------------
# Covariate normalisation
#
# NB: these keyword maps are a STARTING POINT grounded in a sample of the real
# data. The distinct division blobs must be eyeballed and the maps extended
# before the output is trusted — run with --dump-divisions to list them.
# ---------------------------------------------------------------------------

# division_level is a single flat field: the skill ladder and the category/age
# divisions are peers (divisions in their own right, not orthogonal axes). When a
# category type co-occurs with a skill rung (rare, e.g. "Masters Novice"), the
# category wins — it is checked first. Patterns are tried top to bottom; first hit
# wins, so order encodes precedence.
LEVEL_PATTERNS: list[tuple[str, str]] = [
    # Category / age divisions (win over skill rungs — they are the division's
    # identity, e.g. "Masters Novice" → Masters).
    ("Masters", r"\bmaster"),
    ("Sophisticated", r"\bsophisticated\b"),
    ("Junior", r"\bjunior|\byouth\b|\bteen\b"),
    ("Pro-Am", r"\bpro[\s./-]?am\b"),
    ("Invitational", r"\binvitational\b|\binvite\b|\binvitation\b"),
    # All-American and its national variants (All Australian / All Korean / ...).
    ("All-American", r"\ball[\s-]?(american|australian|korean|japanese|canadian|"
                     r"british|irish|ireland|european|french|german|kiwi|aussie|nz|usa)\b"),
    # Skill ladder, highest to lowest (combined rungs like "Advanced/All Star" or
    # "All-Stars/Champions" resolve to the higher one — matched first).
    ("Champions", r"\bchampion|\bchamps?\b"),
    ("All-Star", r"\ball[\s-]?stars?\b|\ballstar"),
    ("Advanced", r"\badvanced?\b|\badv\b"),
    ("Intermediate", r"\bintermediate\b|\binterm\b|\bint\b"),
    ("Novice", r"\bnovice\b|\bnov\b"),
    ("Newcomer", r"\bnewcomer\b|\bnew\b|\brookie\b"),
    ("Open", r"\bopen\b"),
]

FORMAT_PATTERNS: list[tuple[str, str]] = [
    # Strictly (incl. "Switchly Strictly") before J&J.
    ("Strictly", r"\bstrictly\b|\bswitchly\b"),
    ("J&J", r"\bjack\s*[&'n]*\s*jill\b|\bjack\s+and\s+jill\b|\bj\s*&\s*j\b|\bjnj\b|\bjandj\b"),
    ("Classic", r"\bclassic\b|\broutines?\b|\bshowcase\b|\bcabaret\b|\bteam\b"),
]


def _match(patterns: list[tuple[str, str]], text: str) -> str:
    low = text.lower()
    for label, pat in patterns:
        if re.search(pat, low):
            return label
    return "Unknown"


def normalise_level(division_blob: str) -> str:
    return _match(LEVEL_PATTERNS, division_blob)


def normalise_format(division_blob: str) -> str:
    return _match(FORMAT_PATTERNS, division_blob)


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


def make_id(site: str, event_name: str, division_blob: str, used: set[str]) -> str:
    """Build a unique slug id, appending a numeric suffix on collision.

    Disambiguation is against the ids already assigned THIS run only — never disk
    state. Because the manifest is processed in a stable (append-only) order, a
    given scoresheet lands on the same id every run, which is what makes the
    out_path.exists() cache check (and thus idempotency) correct. Using disk
    presence here instead would make a re-run bump the suffix and write a
    duplicate.
    """
    base = "_".join(p for p in (slugify(site), slugify(event_name), slugify(division_blob)) if p)
    base = base or "scoresheet"
    candidate = base
    n = 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


# ---------------------------------------------------------------------------
# Validation (hybrid: crash on integrity bugs, skip on incomplete/too-small data)
# ---------------------------------------------------------------------------

class IntegrityError(Exception):
    """A parsed scoresheet is internally inconsistent — indicates a parser bug."""


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
    IntegrityError (which aborts the run) for violations that signal a parser bug.
    """
    judges = scoresheet.judges
    competitors = scoresheet.competitors
    n = len(competitors)

    # Size floor → skip (legitimately odd source data, not a bug).
    if len(judges) < 2:
        return f"too few judges ({len(judges)})"
    if n < 3:
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


# ---------------------------------------------------------------------------
# Per-scoresheet extraction
# ---------------------------------------------------------------------------

def parse_targets(record: dict, content: bytes) -> list[str | None]:
    """Return the list of `division` arguments to parse for this manifest entry.

    eepro pages are 1:M (one file per division); the other sites are 1:1.
    """
    if record["site"] == "eepro.com":
        names = EeproParser().get_division_names(content)
        return list(names)  # may be empty (e.g. prelims-only page)
    return [None]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dump-divisions",
        action="store_true",
        help="Parse everything and print the distinct division blobs and their "
             "level/format mapping, without writing any parsed files.",
    )
    ap.add_argument("--limit", type=int, default=None, help="Process only the first N manifest entries (debug).")
    args = ap.parse_args()

    records = load_manifest()
    if args.limit:
        records = records[: args.limit]

    if not args.dump_divisions:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)

    used_ids: set[str] = set()
    skips: list[tuple[str, str]] = []  # (label, reason)
    written = 0
    division_audit: list[tuple[str, str, str, str]] = []  # (site, blob, level, format)

    for record in records:
        url = record["url"]
        site = record["site"]
        event_name = record["event_name"]
        event_start = date.fromisoformat(record["event_start"])
        event_end = date.fromisoformat(record["event_end"])
        local_path = Path(record["local_path"])

        if not local_path.exists():
            skips.append((event_name, f"raw file missing: {local_path}"))
            continue

        content = local_path.read_bytes()
        parser = detect_parser(url) or detect_parser_by_content(content, url)
        if parser is None:
            skips.append((event_name, "no parser matched"))
            continue

        try:
            divisions = parse_targets(record, content)
        except Exception as e:
            skips.append((event_name, f"division enumeration failed: {e}"))
            continue
        if not divisions:
            skips.append((event_name, "no finals divisions found"))
            continue

        for div_arg in divisions:
            label = event_name if div_arg is None else f"{event_name} — {div_arg}"
            try:
                scoresheet = parser.parse(url, content, division=div_arg)
            except PrelimsError:
                skips.append((label, "prelims/callback round"))
                continue
            except Exception as e:
                skips.append((label, f"parse error: {type(e).__name__}: {e}"))
                continue

            # Content-level non-finals safety net (numeric prelims that the
            # parser's callback check and the Phase 1 URL filter both missed).
            if looks_like_non_finals(scoresheet.competition_name):
                skips.append((label, "non-finals round (name)"))
                continue

            # Validation: integrity violations raise (abort); soft issues → skip.
            reason = validate(scoresheet)
            if reason is not None:
                skips.append((label, reason))
                continue

            division_blob = isolate_division_blob(
                site, scoresheet.competition_name, event_name, div_arg
            )
            level = normalise_level(division_blob)
            fmt = normalise_format(division_blob)
            division_audit.append((site, division_blob, level, fmt))

            if args.dump_divisions:
                continue

            entry_id = make_id(site, event_name, division_blob, used_ids)
            out_path = PARSED_DIR / f"{entry_id}.json"
            if out_path.exists():
                skips.append((label, "already parsed (cached)"))
                continue

            doc = {
                "id": entry_id,
                "url": url,
                "site": site,
                "event_name": event_name,
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
            logging.info(f"wrote {entry_id}  ({level} / {fmt}, J={doc['num_judges']} C={doc['num_competitors']})")

    # ---- summaries ----
    if args.dump_divisions:
        _print_division_audit(division_audit)
        return

    logging.info(f"Done. Wrote {written} parsed files; skipped {len(skips)}.")
    if skips:
        reason_counts = Counter(re.split(r"[:(]", r, 1)[0].strip() for _, r in skips)
        print("\n=== Skip summary ===")
        for reason, count in reason_counts.most_common():
            print(f"  {count:4d}  {reason}")
        print("\n=== Skips (detail) ===")
        for label, reason in skips:
            print(f"  - {label}: {reason}")


def _print_division_audit(audit: list[tuple[str, str, str, str]]) -> None:
    """Print distinct division blobs and their level/format mapping for review."""
    seen: dict[tuple[str, str], tuple[str, str, int]] = {}
    for site, blob, level, fmt in audit:
        key = (site, blob)
        if key in seen:
            l, f, c = seen[key]
            seen[key] = (l, f, c + 1)
        else:
            seen[key] = (level, fmt, 1)
    print(f"\n=== {len(seen)} distinct division blobs (from {len(audit)} scoresheets) ===\n")
    for (site, blob), (level, fmt, count) in sorted(seen.items()):
        flag = "  <-- UNKNOWN" if level == "Unknown" or fmt == "Unknown" else ""
        print(f"[{site:18}] {level:13} {fmt:9} x{count:<3} {blob!r}{flag}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
