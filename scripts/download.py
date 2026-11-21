#!/usr/bin/env python3
"""Phase 1: Discover and download WCS finals scoresheets to data/raw/.

Discovery logic adapted from who-woulda-won/scripts/check_new_scoresheets.py.
"""

import argparse
import hashlib
import html
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifest.jsonl"
EVENTS_PATH = DATA_DIR / "events.jsonl"

# ---------------------------------------------------------------------------
# Dataclasses and helpers
# (Adapted from who-woulda-won/scripts/check_new_scoresheets.py)
# ---------------------------------------------------------------------------

ROUND_KEYWORDS = re.compile(
    r"^(?:Final|Finals|Semifinal|Semifinals|Semi|Semis|"
    r"Quarterfinal|Quarterfinals|Quarter|Quarters|"
    r"Prelim|Prelims|Preliminary|Preliminaries)$",
    re.IGNORECASE,
)

# Matches dance styles that are definitively not WCS.  Used to skip whole events
# (when the event name contains the keyword) or individual divisions (when only a
# division name does).  "country" catches Country Swing / Line Dance; "silc" catches
# the Ceroc/Modern-Jive SILC Stars competition format.
_NON_WCS_STYLES = r"salsa|bachata|zouk|lindy|hustle|country|silc|brazuka|ceroc|modern\s+jive|shag"
NON_WCS_STYLE_RE = re.compile(rf"\b(?:{_NON_WCS_STYLES})", re.IGNORECASE)
# Division names only: also excludes Blues.  Not applied to event names, because some
# WCS events have "Blues" in the name (e.g. danceconvention.net "Cash&Blues", a WCS
# festival whose J&J divisions are WCS), so an event-level match would drop real WCS.
NON_WCS_DIVISION_RE = re.compile(rf"\b(?:{_NON_WCS_STYLES}|blues\b)", re.IGNORECASE)


@dataclass
class DiscoveredFinal:
    site: str
    event_name: str
    event_date: date
    event_end_date: date
    division: str
    url: str
    parser_division: str | None = None
    event_id: str | None = None         # namespaced: "sd-228", "ee-swinglebell2025", "dc-301126"
    source_event_id: str | None = None  # raw native id: "228", "swinglebell2025", "301126"


def _overlaps(ev_start: date, ev_end: date, w_start: date, w_end: date) -> bool:
    return ev_start <= w_end and ev_end >= w_start


def _decode_nuxt(text: str) -> str:
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)


def _parse_mdy(s: str) -> date | None:
    try:
        parts = s.strip().split("/")
        if len(parts) == 3:
            m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
            return date(2000 + y if y < 100 else y, m, d)
    except (ValueError, IndexError):
        pass
    return None


def _tokenize_js_args(s: str) -> list[str]:
    """Tokenize a JS IIFE argument list (string after the opening paren)."""
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " \t\n":
            i += 1
        elif c == ",":
            i += 1
        elif c == ")":
            break
        elif c == '"':
            j = i + 1
            while j < len(s):
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == '"':
                    j += 1
                    break
                j += 1
            tokens.append(s[i:j])
            i = j
        else:
            j = i
            while j < len(s) and s[j] not in ",)":
                j += 1
            token = s[i:j].strip()
            if token:
                tokens.append(token)
            i = j
    return tokens


def _nuxt_var_map(raw_script: str) -> dict[str, str]:
    """Build a variable→value map from a Nuxt IIFE script tag content.

    Nuxt serialises repeated values as IIFE parameters to save space, e.g.
    (function(a,b,...,C,...){return data})(false,true,...,"6/21/25",...)
    so startDate:C means startDate = "6/21/25".
    """
    try:
        params_end = raw_script.index("){return ")
        params = raw_script[len("window.__NUXT__=(function("):params_end].split(",")
    except ValueError:
        return {}

    # Find where the function body ends by counting braces, skipping string literals
    body_open = raw_script.find("{return ")
    if body_open == -1:
        return {}
    depth = 0
    i = body_open
    args_start = -1
    while i < len(raw_script):
        c = raw_script[i]
        if c == '"':
            i += 1
            while i < len(raw_script):
                if raw_script[i] == "\\":
                    i += 2
                    continue
                if raw_script[i] == '"':
                    break
                i += 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                args_start = i + 2  # skip '}' and '(' to reach first arg
                break
        i += 1

    if args_start == -1:
        return {}

    args = _tokenize_js_args(raw_script[args_start:])
    var_map: dict[str, str] = {}
    for p, a in zip(params, args):
        if a.startswith('"') and a.endswith('"'):
            val = a[1:-1]
            val = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), val)
        else:
            val = a
        var_map[p] = val
    return var_map


# ---------------------------------------------------------------------------
# Rate-limited HTTP client wrapper
# ---------------------------------------------------------------------------

class RateLimitedClient:
    def __init__(self, client: httpx.Client, delay: float = 0.5, retries: int = 3):
        self._client = client
        self._delay = delay
        self._retries = retries
        self._last: dict[str, float] = {}

    def get(self, url: str, **kwargs):
        host = httpx.URL(url).host
        last_exc = None
        for attempt in range(self._retries):
            elapsed = time.monotonic() - self._last.get(host, 0)
            if elapsed < self._delay:
                time.sleep(self._delay - elapsed)
            try:
                result = self._client.get(url, **kwargs)
                self._last[host] = time.monotonic()
                return result
            except (httpx.TimeoutException, httpx.TransportError) as e:
                # Transient network failures (e.g. read timeout) can silently drop a
                # whole event's finals; retry with backoff before giving up.
                last_exc = e
                self._last[host] = time.monotonic()
                if attempt < self._retries - 1:
                    backoff = self._delay * (2 ** attempt)
                    logging.info(
                        f"retrying {url} after {type(e).__name__} "
                        f"(attempt {attempt + 1}/{self._retries}, waiting {backoff:.1f}s)"
                    )
                    time.sleep(backoff)
        raise last_exc


# ---------------------------------------------------------------------------
# Discovery — scoring.dance
# (Adapted from who-woulda-won/scripts/check_new_scoresheets.py)
# ---------------------------------------------------------------------------

def discover_scoring_dance(
    client: RateLimitedClient, w_start: date, w_end: date
) -> list[DiscoveredFinal]:
    finals = []
    logging.info("scoring.dance: fetching /enCA/recent...")
    try:
        html = client.get("https://scoring.dance/enCA/recent").text
    except Exception as e:
        logging.warning(f"scoring.dance: failed to fetch recent page: {e}")
        return finals

    soup = BeautifulSoup(html, "lxml")

    # Matches "05/29 - 06/01/2026" (range) or "04/05/2026" (single date)
    date_range_re = re.compile(r"(\d{2}/\d{2})\s*[-–]\s*(\d{2}/\d{2})/(\d{4})")
    date_single_re = re.compile(r"(\d{2}/\d{2}/\d{4})")
    event_ids: dict[str, tuple[date, date]] = {}
    seen_ids: set[str] = set()

    for a in soup.find_all("a", href=re.compile(r"/events/\d+")):
        href = a.get("href", "")
        m = re.search(r"/events/(\d+)", href)
        if not m or m.group(1) in seen_ids:
            continue
        event_id = m.group(1)
        seen_ids.add(event_id)

        node = a
        found = False
        ev_start = ev_end = None
        for _ in range(5):
            if node is None:
                break
            text = node.get_text(" ", strip=True)
            dm = date_range_re.search(text)
            if dm:
                yr = int(dm.group(3))
                try:
                    ev_start = datetime.strptime(f"{dm.group(1)}/{yr}", "%m/%d/%Y").date()
                    ev_end = datetime.strptime(f"{dm.group(2)}/{yr}", "%m/%d/%Y").date()
                    event_ids[event_id] = (ev_start, ev_end)
                    found = True
                except ValueError:
                    pass
                break
            ds = date_single_re.search(text)
            if ds:
                try:
                    ev_start = ev_end = datetime.strptime(ds.group(1), "%m/%d/%Y").date()
                    event_ids[event_id] = (ev_start, ev_end)
                    found = True
                except ValueError:
                    pass
                break
            node = node.parent

        if not found:
            raw = node.get_text(" ", strip=True)[:80] if node is not None else "(no text found)"
            logging.warning(f"scoring.dance: could not parse date for event {event_id}: {raw!r} (skipping)")
        elif ev_end < w_start:
            break  # events are reverse-chronological; nothing earlier will be in window

    in_window = [
        (eid, es, ee) for eid, (es, ee) in event_ids.items()
        if _overlaps(es, ee, w_start, w_end)
    ]

    if not in_window:
        logging.info(f"scoring.dance: no events in window (checked {len(event_ids)} on page)")
        return finals

    for event_id, ev_start, ev_end in in_window:
        logging.info(f"scoring.dance: event {event_id} ({ev_start} – {ev_end})")
        try:
            r = client.get(f"https://scoring.dance/enCA/events/{event_id}/results/")
            r.raise_for_status()
        except Exception as e:
            logging.warning(f"scoring.dance: failed to fetch results for event {event_id}: {e}")
            continue

        rsoup = BeautifulSoup(r.text, "lxml")
        h1 = rsoup.find("h1")
        event_name = (
            re.sub(r"\s+results?$", "", h1.get_text(strip=True), flags=re.IGNORECASE)
            if h1 else f"Event {event_id}"
        )
        if NON_WCS_STYLE_RE.search(event_name):
            logging.info(f"scoring.dance: skipping non-WCS event {event_name!r}")
            continue
        count = 0
        for a in rsoup.find_all("a", href=re.compile(r"/events/\d+/results/\d+\.html")):
            name = a.get_text(strip=True)
            nl = name.lower()
            if "final" not in nl:
                continue
            if any(x in nl for x in ("prelim", "semi", "quarter")):
                continue
            href = a.get("href", "")
            url = f"https://scoring.dance{href}" if href.startswith("/") else href
            division = re.sub(r"\s+finals?$", "", name, flags=re.IGNORECASE).strip()
            if NON_WCS_DIVISION_RE.search(division):
                logging.info(f"scoring.dance: skipping non-WCS division {division!r} in {event_name!r}")
                continue
            finals.append(DiscoveredFinal(
                site="scoring.dance",
                event_name=event_name,
                event_date=ev_start,
                event_end_date=ev_end,
                division=division,
                url=url,
                event_id=f"sd-{event_id}",
                source_event_id=event_id,
            ))
            count += 1
        logging.info(f"scoring.dance: {event_name} — {count} finals")

    return finals


# ---------------------------------------------------------------------------
# Discovery — eepro.com
# (Adapted from who-woulda-won/scripts/check_new_scoresheets.py)
# Division enumeration removed: one DiscoveredFinal per unique result URL.
# ---------------------------------------------------------------------------

def discover_eepro(
    client: RateLimitedClient, w_start: date, w_end: date
) -> list[DiscoveredFinal]:
    finals = []

    for year in range(w_start.year, w_end.year + 1):
        listing_url = f"https://eepro.com/results/{year}/"
        logging.info(f"eepro.com: fetching results/{year}/...")
        try:
            html = client.get(listing_url).text
        except Exception as e:
            logging.warning(f"eepro.com: failed to fetch {listing_url}: {e}")
            continue

        soup = BeautifulSoup(html, "lxml")
        seen_urls: set[str] = set()

        for li in soup.find_all("li"):
            li_text = li.get_text(" ", strip=True)

            def _parse_month_date(month: str, day: str, year: str) -> date | None:
                s = f"{month} {day} {year}"
                for fmt in ("%B %d %Y", "%b %d %Y"):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except ValueError:
                        continue
                return None

            # Cross-month range: "May 29-June 1, 2025" / "Dec 30-Jan 3, 2026".
            # The year applies to the end date; if the start month falls after the
            # end month (Dec→Jan), the start belongs to the previous year.
            dm_cross = re.search(
                r"([A-Za-z]+)\s+(\d+)\s*[-–]\s*([A-Za-z]+)\s+(\d+),?\s*(\d{4})", li_text
            )
            # Same-month range: "June 26-29, 2025".
            dm = re.search(r"([A-Za-z]+)\s+(\d+)\s*[-–]\s*(\d+),?\s*(\d{4})", li_text)
            if dm_cross:
                year = dm_cross.group(5)
                ev_start = _parse_month_date(dm_cross.group(1), dm_cross.group(2), year)
                ev_end = _parse_month_date(dm_cross.group(3), dm_cross.group(4), year)
                if ev_start is not None and ev_end is not None and ev_start > ev_end:
                    ev_start = _parse_month_date(
                        dm_cross.group(1), dm_cross.group(2), str(int(year) - 1)
                    )
                if ev_start is None or ev_end is None:
                    continue
            elif dm:
                ev_start = _parse_month_date(dm.group(1), dm.group(2), dm.group(4))
                ev_end = _parse_month_date(dm.group(1), dm.group(3), dm.group(4))
                if ev_start is None or ev_end is None:
                    continue
            else:
                dm2 = re.search(r"([A-Za-z]+)\s+(\d+),?\s*(\d{4})", li_text)
                if not dm2:
                    continue
                ev_start = _parse_month_date(dm2.group(1), dm2.group(2), dm2.group(3))
                if ev_start is None:
                    continue
                ev_end = ev_start

            if not _overlaps(ev_start, ev_end, w_start, w_end):
                continue

            # Event name is in the <label> tag: "June 26-29, 2025 - Liberty Swing"
            label = li.find("label")
            label_text = label.get_text(strip=True) if label else ""
            name_parts = re.split(r"\d{4}\s*[-–]\s*", label_text, maxsplit=1)
            event_name = name_parts[1].strip() if len(name_parts) > 1 else ""

            if NON_WCS_STYLE_RE.search(event_name):
                logging.info(f"eepro.com: skipping non-WCS event {event_name!r}")
                continue

            for a in li.find_all("a", href=True):
                href = a.get("href", "")
                link_text = a.get_text(strip=True)
                m = re.search(
                    r"(?:\.\./|/results/)([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+?)(?:\.html)?$",
                    href,
                )
                if not m:
                    continue
                event_slug = m.group(1)
                result_type = m.group(2).lower()
                # Skip non-finals rounds
                if re.search(r"prelim|semi|quarter|heat", result_type):
                    continue
                # Keep only relevant competition types (J&J variants, Strictly, All-American)
                if not re.search(r"jj|jack|strictly|american", result_type):
                    continue
                if NON_WCS_DIVISION_RE.search(link_text):
                    logging.info(f"eepro.com: skipping non-WCS division {link_text!r} in {event_name!r}")
                    continue

                result_url = f"https://eepro.com/results/{event_slug}/{m.group(2)}.html"
                if result_url in seen_urls:
                    continue
                seen_urls.add(result_url)

                finals.append(DiscoveredFinal(
                    site="eepro.com",
                    event_name=event_name or event_slug,
                    event_date=ev_start,
                    event_end_date=ev_end,
                    division="",
                    url=result_url,
                    event_id=f"ee-{event_slug}",
                    source_event_id=event_slug,
                ))
                logging.info(f"eepro.com: {event_name} — {link_text} ({ev_start} – {ev_end})")

    return finals


# ---------------------------------------------------------------------------
# Discovery — danceconvention.net
# (Adapted from who-woulda-wonscripts/check_new_scoresheets.py)
# ---------------------------------------------------------------------------

def discover_danceconvention(
    client: RateLimitedClient, w_start: date, w_end: date
) -> list[DiscoveredFinal]:
    finals = []

    # Regex pieces for fields that may be a quoted literal or a variable reference
    _date_or_var = r'(?:"([^"]+)"|([a-zA-Z_$][a-zA-Z0-9_$]*))'

    for year in range(w_start.year, w_end.year + 1):
        archive_url = f"https://danceconvention.net/eventdirector/en/eventsarchive/{year}"
        logging.info(f"danceconvention.net: fetching archive ({year})...")
        try:
            resp = client.get(archive_url)
            resp.raise_for_status()
        except Exception as e:
            logging.warning(f"danceconvention.net: failed to fetch archive {year}: {e}")
            continue

        raw_html = resp.text

        # Build variable map to resolve IIFE parameter references (e.g. startDate:C → "6/21/25")
        nuxt_start = raw_html.find("window.__NUXT__=(function(")
        var_map = _nuxt_var_map(raw_html[nuxt_start:]) if nuxt_start != -1 else {}
        if not var_map:
            logging.warning("danceconvention.net: could not build Nuxt variable map; dates may be missing")

        blob = _decode_nuxt(raw_html)

        def resolve_date_field(m: re.Match) -> str | None:
            """Return the string value of a date field match (literal or variable)."""
            literal, var = m.group(1), m.group(2)
            if literal:
                return literal
            return var_map.get(var)

        events: dict[str, tuple[str, str, date, date]] = {}
        event_name_re = re.compile(r'eventId:(\d+),name:"([^"]*)"')

        for em in event_name_re.finditer(blob):
            event_id, event_name = em.group(1), html.unescape(em.group(2))
            if event_id in events:
                continue

            # Look forward ~600 chars for startDate, endDate, eventPage
            ctx = blob[em.start(): em.start() + 600]

            start_m = re.search(r"startDate:" + _date_or_var, ctx)
            end_m = re.search(r"endDate:" + _date_or_var, ctx)

            ev_start = ev_end = None
            if start_m:
                s = resolve_date_field(start_m)
                ev_start = _parse_mdy(s) if s else None
            if end_m:
                s = resolve_date_field(end_m)
                ev_end = _parse_mdy(s) if s else None
            if ev_end is None:
                ev_end = ev_start

            if ev_start is None:
                logging.warning(
                    f"danceconvention.net: could not parse date for event {event_id} "
                    f"({event_name!r}), skipping"
                )
                continue

            page_m = re.search(
                rf'eventPage:"/eventdirector/en/eventpage/{event_id}-([^"]+)"', ctx
            )
            if not page_m:
                continue
            slug = page_m.group(1)

            events[event_id] = (event_name, slug, ev_start, ev_end)

        qualifying = [
            (eid, name, slug, es, ee)
            for eid, (name, slug, es, ee) in events.items()
            if _overlaps(es, ee, w_start, w_end)
        ]
        logging.info(
            f"danceconvention.net: found {len(events)} events, {len(qualifying)} in window"
        )

        for event_id, event_name, slug, ev_start, ev_end in qualifying:
            if NON_WCS_STYLE_RE.search(event_name):
                logging.info(f"danceconvention.net: skipping non-WCS event {event_name!r}")
                continue
            results_url = (
                f"https://danceconvention.net/eventdirector/en/"
                f"eventpage/{event_id}-{slug}/results"
            )
            logging.info(f"danceconvention.net: {event_name} ({ev_start} – {ev_end})")
            try:
                resp = client.get(results_url)
                resp.raise_for_status()
            except Exception as e:
                logging.warning(
                    f"danceconvention.net: failed to fetch results for {event_name}: {e}"
                )
                continue

            rblob = _decode_nuxt(resp.text)

            # Every real division entry in the Nuxt data is preceded by a numeric division ID:
            #   div_id,"Division Name",[opt "TYPE_CODE",]pdf_id,[opt "Round Name",]"/URL"
            # Per-couple/per-person scoresheets have no preceding division ID — they start
            # directly with a quoted name — so anchoring on \d+," naturally excludes them.
            # Formats:
            #   A: div_id,"Division",pdf_id,"/URL"
            #   B: div_id,"Division",pdf_id,"Round Name","/URL"
            #   D: div_id,"Division","TYPE_CODE",pdf_id,"/URL"         (e.g. RANDOM_COUPLE)
            #   D+B: div_id,"Division","TYPE_CODE",pdf_id,"Round Name","/URL"
            div_re = re.compile(
                r'\d+,"([^"]+)",(?:"([^"]+)",)?(\d+),(?:"([^"]+)",)?"/eventdirector/en/roundscores/\d+\.pdf"'
            )
            # "final" (Latin) and "Финал" (Cyrillic) both signal a finals round.
            # NON_FINALS covers semi/prelim/quarter in Latin and Отбор (qualifier) in Cyrillic.
            # Полуфинал/Четвертьфинал contain финал as a substring so are listed explicitly.
            FINALS_IN_NAME = re.compile(r"\bfinal|финал", re.IGNORECASE)
            NON_FINALS = re.compile(
                r"\b(?:semi|prelim|quarter|heat)\b|отбор|полуфинал|четвертьфинал", re.IGNORECASE
            )
            count = 0
            for m in div_re.finditer(rblob):
                division_name, pre_field, pdf_id, round_name = (
                    html.unescape(m.group(1)), m.group(2), m.group(3), m.group(4)
                )
                # Guard against spurious matches where the "division name" is actually a URL path
                if division_name.startswith('/'):
                    continue
                if round_name is not None:
                    # Format B / D+B: filter by round name
                    if not FINALS_IN_NAME.search(round_name) or NON_FINALS.search(round_name):
                        continue
                else:
                    # Format A / D: skip entries where the "division name" is actually a round keyword
                    if ROUND_KEYWORDS.match(division_name.strip()):
                        continue
                if NON_WCS_DIVISION_RE.search(division_name):
                    logging.info(f"danceconvention.net: skipping non-WCS division {division_name!r} in {event_name!r}")
                    continue
                finals.append(DiscoveredFinal(
                    site="danceconvention.net",
                    event_name=event_name,
                    event_date=ev_start,
                    event_end_date=ev_end,
                    division=division_name,
                    url=f"https://danceconvention.net/eventdirector/en/roundscores/{pdf_id}.pdf",
                    event_id=f"dc-{event_id}",
                    source_event_id=event_id,
                ))
                count += 1
            logging.info(f"danceconvention.net: {event_name} — {count} finals found")

    return finals


# ---------------------------------------------------------------------------
# Manifest and download helpers
# ---------------------------------------------------------------------------

def url_to_filename(url: str) -> str:
    digest = hashlib.md5(url.encode()).hexdigest()
    ext = ".pdf" if url.lower().endswith(".pdf") else ".html"
    return f"{digest}{ext}"


def load_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.exists():
        return {}
    manifest = {}
    for line in MANIFEST_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            record = json.loads(line)
            manifest[record["url"]] = record
    return manifest


def append_manifest(record: dict) -> None:
    with MANIFEST_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")


def download_and_record(
    client: RateLimitedClient, final: DiscoveredFinal, manifest: dict,
    dry_run: bool = False,
) -> None:
    label = final.event_name
    if final.division:
        label += f" — {final.division}"

    if final.url in manifest:
        logging.info(f"Already cached: {label} | {final.url}")
        return

    if dry_run:
        logging.info(f"[DRY RUN] Would download: {label} | {final.url}")
        return

    filename = url_to_filename(final.url)
    local_path = RAW_DIR / filename

    if not local_path.exists():
        try:
            resp = client.get(final.url)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
            logging.info(f"Downloaded: {final.url}")
        except Exception as e:
            logging.warning(f"Failed to download {final.url}: {e}")
            return

    record = {
        "url": final.url,
        "site": final.site,
        "event_id": final.event_id,
        "source_event_id": final.source_event_id,
        "event_name": final.event_name,
        "event_start": final.event_date.isoformat(),
        "event_end": final.event_end_date.isoformat(),
        "local_path": str(local_path),
    }
    append_manifest(record)
    manifest[final.url] = record


# ---------------------------------------------------------------------------
# Events dimension table
# ---------------------------------------------------------------------------

def write_events_jsonl(manifest: dict) -> None:
    """Rebuild data/events.jsonl from the manifest (one row per unique event_id)."""
    events: dict[str, dict] = {}
    for rec in manifest.values():
        eid = rec.get("event_id")
        if not eid or eid in events:
            continue
        events[eid] = {
            "event_id": eid,
            "site": rec["site"],
            "source_event_id": rec.get("source_event_id"),
            "event_name": rec["event_name"],
            "event_start": rec["event_start"],
            "event_end": rec["event_end"],
        }
    with EVENTS_PATH.open("w") as f:
        for ev in events.values():
            f.write(json.dumps(ev) + "\n")
    logging.info(f"Wrote {len(events)} events to {EVENTS_PATH.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Discover and download WCS finals scoresheets."
    )
    ap.add_argument(
        "--site",
        choices=["scoring.dance", "eepro", "danceconvention"],
        action="append",
        dest="sites",
        help="Only collect from this site (repeatable; default: all three)",
    )
    ap.add_argument(
        "--start",
        type=date.fromisoformat,
        default=date(2025, 1, 1),
        help="Start date YYYY-MM-DD (default: 2025-01-01)",
    )
    ap.add_argument(
        "--end",
        type=date.fromisoformat,
        default=date(2025, 12, 31),
        help="End date YYYY-MM-DD (default: 2025-12-31)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover and print what would be downloaded without writing any files",
    )
    args = ap.parse_args()

    w_start = args.start
    w_end = args.end
    sites = set(args.sites or ["scoring.dance", "eepro", "danceconvention"])

    if not args.dry_run:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    logging.info(f"Date window: {w_start} to {w_end}")
    logging.info(f"Sites: {', '.join(sorted(sites))}")
    if args.dry_run:
        logging.info("DRY RUN — no files will be downloaded or written")
    else:
        logging.info(f"Manifest: {len(manifest)} entries already cached")

    site_fns = {
        "scoring.dance": discover_scoring_dance,
        "eepro": discover_eepro,
        "danceconvention": discover_danceconvention,
    }

    with httpx.Client(timeout=30, follow_redirects=True) as http_client:
        client = RateLimitedClient(http_client, delay=0.5)

        for site in sorted(sites):
            logging.info(f"--- {site} ---")
            try:
                finals = site_fns[site](client, w_start, w_end)
            except Exception as e:
                logging.warning(f"{site}: discovery failed unexpectedly: {e}")
                continue

            logging.info(f"{site}: discovered {len(finals)} finals")
            before = len(manifest)
            for final in finals:
                download_and_record(client, final, manifest, dry_run=args.dry_run)
            if not args.dry_run:
                logging.info(f"{site}: {len(manifest) - before} new files downloaded")

    if args.dry_run:
        logging.info("DRY RUN complete — nothing written.")
    else:
        write_events_jsonl(manifest)
        logging.info(f"Done. Manifest now has {len(manifest)} entries.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
