#!/usr/bin/env python3
"""Phase 4 / Task 4A: Build lookups/regions.json — a geographic region per event.

Region is resolved as a lookup/join problem, not an interpretation problem:

  1. Match each distinct event against the WSDC event registry
     (https://worldsdc.com/events/), which carries authoritative city/state/country.
  2. Fall back to scoring.dance's own embedded JSON-LD location for any of its events
     the registry misses.
  3. Route the genuine residual to lookups/regions-manual.csv — a durable, idempotent
     worklist a human or agent fills in, after which a re-run folds it in.

Stored values are ISO 3166 codes (country = alpha-2, US state = ISO 3166-2 like "US-CA");
display names are derived on demand with pycountry, never stored.

Output: lookups/regions.json, one entry per event_id (the analysis join key).
"""

import argparse
import csv
import json
import logging
import re
import time
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import httpx
import pycountry
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PARSED_DIR = DATA_DIR / "parsed"
RAW_DIR = DATA_DIR / "raw"
REGISTRY_CACHE = DATA_DIR / "wsdc-events.html"
LOOKUPS_DIR = PROJECT_ROOT / "lookups"
REGIONS_PATH = LOOKUPS_DIR / "regions.json"
MANUAL_PATH = LOOKUPS_DIR / "regions-manual.csv"

REGISTRY_URL = "https://worldsdc.com/events/"
USER_AGENT = "Mozilla/5.0 (wcs-judge-agreement research)"

MANUAL_FIELDS = [
    "event_id", "event_name", "site", "event_date", "url",
    "registry_candidate", "country_iso2", "us_state_iso", "filled_by", "notes",
]
# filled_by -> the `source` recorded in regions.json, so that rows an agent researched
# are distinguishable from rows a human has filled or verified.
MANUAL_SOURCES = {"agent": "manual-agent", "human": "manual-human"}
MANUAL_README = (
    "Worklist for events whose region could not be resolved automatically. "
    "Fill country_iso2 (ISO 3166-1 alpha-2, e.g. US, HU, NZ) on each blank row; "
    "for US events also fill us_state_iso (ISO 3166-2, e.g. US-CA). "
    "Set filled_by to 'agent' or 'human' on every filled row (change 'agent' to 'human' "
    "once a person has checked it), and give the evidence in notes. "
    "Use event_name/url/registry_candidate for context. Re-run build_regions.py when done. "
    "Filled rows are authoritative and are never overwritten."
)

# ---------------------------------------------------------------------------
# Country / US-state canonicalisation (-> ISO 3166 codes)
# ---------------------------------------------------------------------------

# Variants the sources emit that pycountry's `name` lookup does not resolve directly.
COUNTRY_ALIASES = {
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "us": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "czechia": "CZ",
    "czech republic": "CZ",
    "the netherlands": "NL",
}


def canonicalize_country(name):
    """Return ISO 3166-1 alpha-2 for a country name, or None if unresolved."""
    if not name:
        return None
    key = name.strip().lower()
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    for getter in ("name", "official_name", "common_name"):
        try:
            c = pycountry.countries.get(**{getter: name.strip()})
        except Exception:
            c = None
        if c:
            return c.alpha_2
    return None


def _build_us_state_map():
    """Map US state full names and 2-letter abbreviations -> ISO 3166-2 (e.g. 'US-CA')."""
    m = {}
    for sub in pycountry.subdivisions:
        if sub.country_code == "US":
            m[sub.name.lower()] = sub.code
            m[sub.code.split("-")[1].lower()] = sub.code
    return m


US_STATE_MAP = _build_us_state_map()


def canonicalize_us_state(name):
    """Return ISO 3166-2 code (e.g. 'US-CA') for a US state name/abbrev, or None."""
    if not name:
        return None
    return US_STATE_MAP.get(name.strip().lower())


# ---------------------------------------------------------------------------
# Name normalisation and fuzzy matching
# ---------------------------------------------------------------------------

# Generic tokens that carry no geographic signal; dropped before matching so that
# e.g. "Scandinavian Open WCS" and "Scandinavian Open WCS SNOW" collapse together.
_FILLER = {
    "wcs", "west", "coast", "swing", "dance", "festival",
    "convention", "championship", "championships", "open", "the",
}


def norm(name):
    """Normalise an event name for matching: fold case/diacritics, drop years,
    parentheticals, the registry 'Registry/Trial Event' suffix, and filler words."""
    s = name.casefold()
    s = re.sub(r"registry event|trial event", " ", s)
    s = re.sub(r"\(.*?\)", " ", s)                       # parentheticals
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # strip accents
    s = re.sub(r"\b(19|20)\d\d\b", " ", s)               # 4-digit years
    s = re.sub(r"[^a-z0-9]+", " ", s)
    tokens = [t for t in s.split() if t not in _FILLER]
    return " ".join(tokens).strip()


def token_set(normalized):
    return set(normalized.split())


def containment_score(a, b):
    """|A ∩ B| / min(|A|, |B|): high when one token set is a subset of the other."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# ---------------------------------------------------------------------------
# WSDC registry: fetch + parse
# ---------------------------------------------------------------------------


def fetch_registry(refresh=False):
    """Return the registry HTML, cached to data/wsdc-events.html."""
    if REGISTRY_CACHE.exists() and not refresh:
        logging.info(f"Using cached registry: {REGISTRY_CACHE}")
        return REGISTRY_CACHE.read_text(encoding="utf-8")
    logging.info(f"Fetching {REGISTRY_URL}")
    with httpx.Client(timeout=30, follow_redirects=True,
                      headers={"User-Agent": USER_AGENT}) as client:
        time.sleep(0.5)  # politeness
        resp = client.get(REGISTRY_URL)
        resp.raise_for_status()
    REGISTRY_CACHE.write_text(resp.text, encoding="utf-8")
    return resp.text


def parse_location_string(loc):
    """Split a registry location string into (city, state_raw, country_raw).

    Country is the last comma-separated part. For US rows the state is the
    second-to-last part (handles 'Washington, DC, VA, USA'); for other countries
    everything before the country is the city.
    """
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if not parts:
        return (None, None, None)
    country = parts[-1]
    city = parts[0] if len(parts) > 1 else None
    # US rows carry the state as the second-to-last part (handles 'Washington, DC, VA, USA').
    if canonicalize_country(country) == "US" and len(parts) >= 2:
        return (city, parts[-2], country)
    return (city, None, country)


def parse_registry_table(html):
    """Parse the registry page into a list of dicts: raw_name, city, state_raw, country_raw."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        raise ValueError("no <table> found on registry page")
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) < 3 or cells[0].lower() == "date":
            continue
        # Cell 1 = name with a glued "Registry Event"/"Trial Event" suffix; cell 2 = location.
        name = re.sub(r"\s*(Registry|Trial) Event\s*$", "", cells[1]).strip()
        city, state_raw, country_raw = parse_location_string(cells[2])
        if not name or not country_raw:
            continue
        rows.append({
            "raw_name": name, "city": city,
            "state_raw": state_raw, "country_raw": country_raw,
        })
    return rows


def build_registry_index(rows):
    """norm(name) -> list of registry rows sharing that normalised name."""
    index = {}
    for r in rows:
        index.setdefault(norm(r["raw_name"]), []).append(r)
    return index


def registry_token_counts(index):
    """How many distinct registry names each token appears in (for distinctiveness)."""
    counts = Counter()
    for key in index:
        for tok in token_set(key):
            counts[tok] += 1
    return counts


def fuzzy_accept(event_norm, key_norm, token_counts):
    """Whether a fuzzy match between two normalised names is confident enough.

    Accept on any of: high overall string similarity; strong token containment with at
    least two shared tokens; or a single shared token that is long (>=8 chars) and unique
    in the registry (catches subtitle variants like 'Flowstate' while rejecting generic
    single-word collisions like 'cash').
    """
    a, b = token_set(event_norm), token_set(key_norm)
    shared = a & b
    if not shared:
        return False
    if SequenceMatcher(None, event_norm, key_norm).ratio() >= 0.82:
        return True
    if containment_score(a, b) >= 0.85 and len(shared) >= 2:
        return True
    if containment_score(a, b) == 1.0 and len(shared) == 1:
        tok = next(iter(shared))
        if len(tok) >= 8 and token_counts.get(tok, 0) == 1:
            return True
    return False


def match_event(event_name, index, token_counts):
    """Match an event name against the registry index.

    Returns (row, kind, matched_name) where kind is 'wsdc-registry-exact',
    'wsdc-registry-fuzzy', or (None, None, None) if no confident match. A normalised
    name that maps to rows with conflicting countries is treated as no match.
    """
    n = norm(event_name)
    if not n:
        return (None, None, None)

    def _resolve(candidates):
        countries = {canonicalize_country(r["country_raw"]) for r in candidates}
        if len(countries) != 1 or None in countries:
            return None  # ambiguous / unresolvable country -> caller treats as miss
        return candidates[0]

    if n in index:
        row = _resolve(index[n])
        if row:
            return (row, "wsdc-registry-exact", row["raw_name"])

    # Among keys that pass the acceptance predicate, take the highest string similarity.
    best, best_ratio = None, 0.0
    for key in index:
        if fuzzy_accept(n, key, token_counts):
            r = SequenceMatcher(None, n, key).ratio()
            if r > best_ratio:
                best, best_ratio = key, r
    if best is not None:
        row = _resolve(index[best])
        if row:
            return (row, "wsdc-registry-fuzzy", row["raw_name"])
    return (None, None, None)


# ---------------------------------------------------------------------------
# scoring.dance JSON-LD fallback
# ---------------------------------------------------------------------------

_LOCATION_RE = re.compile(r'"location":(\{"@type":"Place"[^}]*\})')


def extract_scoring_dance_location(raw_text):
    """Pull (city, country_raw) from scoring.dance JSON-LD, or (None, None)."""
    m = _LOCATION_RE.search(raw_text)
    if not m:
        return (None, None)
    try:
        place = json.loads(m.group(1))
    except json.JSONDecodeError:
        return (None, None)
    city = place.get("name") or None
    country = place.get("country") or None
    return (city, country)


# ---------------------------------------------------------------------------
# Event loading
# ---------------------------------------------------------------------------


def load_events():
    """One record per distinct event_id from data/parsed/*.json."""
    events = {}
    for f in sorted(PARSED_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        eid = d.get("event_id")
        if eid and eid not in events:
            events[eid] = {
                "event_id": eid,
                "event_name": d.get("event_name", ""),
                "site": d.get("site", ""),
                "event_date": d.get("event_date", ""),
                "url": d.get("url", ""),
                "raw_file": d.get("raw_file", ""),
            }
    return events


# ---------------------------------------------------------------------------
# Manual worklist (CSV) round-trip
# ---------------------------------------------------------------------------


def _is_filled(row):
    """A manual row is complete when country is set and (non-US, or US state is set)."""
    country = (row.get("country_iso2") or "").strip()
    if not country:
        return False
    if country == "US":
        return bool((row.get("us_state_iso") or "").strip())
    return True


def manual_source(row):
    """The `source` value for a filled manual row; raises if filled_by is missing or invalid."""
    filled_by = (row.get("filled_by") or "").strip().lower()
    if filled_by not in MANUAL_SOURCES:
        raise ValueError(
            f"{MANUAL_PATH.name}: filled row {row.get('event_id')} has filled_by="
            f"{filled_by!r}; expected one of {sorted(MANUAL_SOURCES)}")
    return MANUAL_SOURCES[filled_by]


def load_manual():
    """Read lookups/regions-manual.csv -> {event_id: row dict}. Skips the README row."""
    manual = {}
    if not MANUAL_PATH.exists():
        return manual
    with MANUAL_PATH.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            eid = (row.get("event_id") or "").strip()
            if eid and eid != "_README":
                manual[eid] = row
    return manual


def write_manual(rows):
    """Write the worklist with the README first and unfilled (todo) rows floated to the top."""
    LOOKUPS_DIR.mkdir(exist_ok=True)
    ordered = sorted(rows, key=lambda r: (_is_filled(r), r.get("site", ""),
                                          r.get("event_name", "")))
    with MANUAL_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANUAL_FIELDS)
        writer.writeheader()
        writer.writerow({"event_id": "_README", "event_name": MANUAL_README})
        for r in ordered:
            writer.writerow({k: r.get(k, "") for k in MANUAL_FIELDS})


# ---------------------------------------------------------------------------
# Main resolution
# ---------------------------------------------------------------------------


def display_country(alpha2):
    c = pycountry.countries.get(alpha_2=alpha2) if alpha2 else None
    return c.name if c else (alpha2 or "?")


def display_state(code):
    s = pycountry.subdivisions.get(code=code) if code else None
    return s.name if s else (code or "")


def resolve_all(events, index, token_counts):
    """Resolve every event to ISO codes via registry -> scoring.dance JSON-LD -> manual.

    Returns (regions, manual_rows) where regions maps event_id -> entry dict and
    manual_rows is the full set of worklist rows to persist.
    """
    manual = load_manual()
    regions = {}
    manual_rows = {}  # event_id -> row (preserve existing filled rows verbatim)

    for eid, ev in events.items():
        name, site = ev["event_name"], ev["site"]
        country = state = source = matched = None
        wsdc_registered = False

        # 1 & 2: registry match
        row, kind, matched = match_event(name, index, token_counts)
        if row:
            country = canonicalize_country(row["country_raw"])
            state = canonicalize_us_state(row["state_raw"]) if country == "US" else None
            source = kind
            wsdc_registered = True

        # 3: scoring.dance JSON-LD: fallback, and cross-check on the registry match (no
        # state available from this source). If the two disagree on country, trust neither
        # (either can be wrong) and leave the event for the manual worklist.
        conflict = ""
        if site == "scoring.dance" and ev["raw_file"]:
            raw_path = RAW_DIR / ev["raw_file"]
            if raw_path.exists():
                _, country_raw = extract_scoring_dance_location(
                    raw_path.read_text(encoding="utf-8", errors="replace"))
                c = canonicalize_country(country_raw)
                if c and country is None:
                    country, source = c, "scoring-dance-jsonld"
                elif c and c != country:
                    conflict = f"conflict: registry says {country}, scoring.dance says {c}"
                    country = state = source = None
                    wsdc_registered = False

        # 4: manual override / completion. A filled manual row is authoritative.
        man = manual.get(eid)
        if man and _is_filled(man):
            country = (man.get("country_iso2") or "").strip()
            state = (man.get("us_state_iso") or "").strip() or None
            source = manual_source(man)
            matched = None

        # Determine whether the event is fully resolved (US requires a state).
        resolved = country is not None and (country != "US" or state is not None)

        if resolved:
            regions[eid] = {
                "event_name": name,
                "site": site,
                "country": country,
                "state": state,
                "source": source,
                "matched_name": matched,
                "wsdc_registered": wsdc_registered,
            }
        else:
            # Seed/carry a worklist row. Pre-fill any partial auto result (e.g. US country
            # known but state unresolved) so the human only has to complete the gap.
            base = man if (man and not _is_filled(man)) else {}
            manual_rows[eid] = {
                "event_id": eid,
                "event_name": name,
                "site": site,
                "event_date": ev["event_date"],
                "url": ev["url"],
                "registry_candidate": matched or base.get("registry_candidate", ""),
                "country_iso2": base.get("country_iso2", "") or (country or ""),
                "us_state_iso": base.get("us_state_iso", "") or (state or ""),
                "filled_by": base.get("filled_by", ""),
                "notes": base.get("notes", "") or conflict,
            }

    # Preserve every already-filled manual row, even for events no longer present, so a
    # human's work is never lost; filled rows for current events are already in `regions`.
    for eid, man in manual.items():
        if eid not in manual_rows and not _is_filled(man):
            continue
        manual_rows.setdefault(eid, {k: man.get(k, "") for k in MANUAL_FIELDS})

    return regions, manual_rows


def main():
    parser = argparse.ArgumentParser(description="Build lookups/regions.json (Task 4A).")
    parser.add_argument("--refresh", action="store_true",
                        help="re-fetch the WSDC registry instead of using the cache")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    events = load_events()
    logging.info(f"Loaded {len(events)} distinct events from {PARSED_DIR}")

    rows = parse_registry_table(fetch_registry(refresh=args.refresh))
    logging.info(f"Parsed {len(rows)} registry rows")
    index = build_registry_index(rows)
    token_counts = registry_token_counts(index)

    regions, manual_rows = resolve_all(events, index, token_counts)

    LOOKUPS_DIR.mkdir(exist_ok=True)
    REGIONS_PATH.write_text(
        json.dumps(dict(sorted(regions.items())), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    write_manual(list(manual_rows.values()))

    # ---- Report -----------------------------------------------------------
    by_source = {}
    for entry in regions.values():
        by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1
    unresolved = [eid for eid, r in manual_rows.items() if not _is_filled(r)]

    logging.info("--- summary ---")
    for src in sorted(by_source):
        logging.info(f"  {src:24} {by_source[src]}")
    logging.info(f"  {'unresolved (worklist)':24} {len(unresolved)}")
    logging.info(f"Wrote {REGIONS_PATH} ({len(regions)} events)")
    logging.info(f"Wrote {MANUAL_PATH} ({len(manual_rows)} rows, {len(unresolved)} to fill)")

    fuzzy = [(eid, r) for eid, r in regions.items()
             if r["source"] == "wsdc-registry-fuzzy"]
    if fuzzy:
        logging.info(f"--- fuzzy matches to eyeball ({len(fuzzy)}) ---")
        for eid, r in sorted(fuzzy):
            loc = display_country(r["country"]) + (
                f" / {display_state(r['state'])}" if r["state"] else "")
            logging.info(f"  {r['event_name']!r} -> {r['matched_name']!r}  [{loc}]")
    if unresolved:
        logging.info(f"--- unresolved, see {MANUAL_PATH.name} ({len(unresolved)}) ---")
        for eid in sorted(unresolved):
            logging.info(f"  {eid}  {manual_rows[eid]['event_name']!r}")


if __name__ == "__main__":
    main()
