# Debugging Brief: download.py Discovery Validation

## Project context

This is `wcs-judge-divergence`, a project to quantify judge disagreement in WCS (West Coast Swing) competition finals. Phase 1 is `scripts/download.py`, which discovers and downloads raw scoresheets from three websites into `data/raw/` with a manifest at `data/manifest.jsonl`.

The script is working but has had several bugs fixed already, and likely has more. Your job is to systematically validate discovery output against the actual list pages, month by month through 2025, and fix any discrepancies you find.

## Setup

```bash
cd /home/czlee/wcs-judge-divergence
# venv already exists
venv/bin/python scripts/download.py --help
```

## The three sites

| Site | List/menu page | What it links to |
|---|---|---|
| `scoring.dance` | `https://scoring.dance/enCA/recent` | Per-division HTML results pages |
| `eepro.com` | `https://eepro.com/results/2025/` | Per-event HTML results pages |
| `danceconvention.net` | `https://danceconvention.net/eventdirector/en/eventsarchive/2025` | Per-event results pages → PDF scoresheets |

## The process

**Goal:** ensure that for every month, everything that *should* be discovered is discovered, and nothing that *shouldn't* be is included.

**Steps for each month:**

1. Run a dry run for that month across all three sites:
   ```bash
   venv/bin/python scripts/download.py --start 2025-MM-01 --end 2025-MM-30 --dry-run 2>&1
   ```
   (adjust end date for the actual month length)

2. Download and inspect the list/menu pages for each site. **Save local copies** so you don't keep hitting the network — they're large and you'll refer to them repeatedly:
   ```bash
   # scoring.dance — one page covers all months
   curl -o /tmp/scoring_dance_recent.html https://scoring.dance/enCA/recent

   # eepro — one page covers all of 2025
   curl -o /tmp/eepro_2025.html https://eepro.com/results/2025/

   # danceconvention — one page covers all of 2025
   curl -o /tmp/dc_archive_2025.html https://danceconvention.net/eventdirector/en/eventsarchive/2025
   ```
   You only need to download these once (or refresh if stale).

3. For the month under review, manually identify which events appear on the list pages and what finals/results links they have. Compare against the dry-run output. Look for:
   - Events on the list page that don't appear in the dry-run output (missed events)
   - Events in the dry-run output that look wrong (wrong name, wrong date, unexpected URL)
   - Results links on the list page that the script skipped but shouldn't have (or vice versa)

4. For danceconvention.net, also spot-check individual event results pages when the archive page shows an event but the dry-run shows 0 finals for it.

5. Fix bugs, re-run, repeat until the month looks correct. Then move to the next month.

**Do not trigger real downloads** — always use `--dry-run`. The script will still fetch list/menu pages during discovery (that's unavoidable), but it won't write any files to `data/raw/` or `data/manifest.jsonl`.

## Bugs already fixed (do not re-introduce)

- **eepro date parsing**: months Jan–Apr use abbreviated names ("Jan", "Apr") but `strptime` was using `%B` (full names only). Fixed to try both `%B` and `%b`.
- **eepro URL filter**: was `endswith("finals")` which missed pages like `strictlyswing.html`. Fixed to: skip if slug contains `prelim|semi|quarter|heat`; keep if slug contains `jj|jack|strictly|american`.
- **eepro event name**: was fetching each result page during discovery to extract the `<h2>`. This double-hit every page. Fixed to extract name from `<label>` tag on the listing page instead.
- **danceconvention event names**: regex was looking for `,{event_id},"name"` but Nuxt format is `eventId:{event_id},name:"name"`. Fixed.
- **danceconvention date parsing**: Nuxt IIFE serialisation stores repeated values as parameter references (e.g. `startDate:C` where `C="6/21/25"`). Fixed with `_nuxt_var_map()` helper.
- **danceconvention results format variant**: some events (e.g. Australian Classic) use `"Division",pdf_id,"ROUND NAME","/URL"` instead of `"Division",pdf_id,"/URL"`. The old regex didn't match the variant with a round name. Fixed with updated regex and round-name-based filtering.

## Bugs fixed in session 2 (Jan–Mar 2025 validation pass)

- **danceconvention context window too small**: the script looks at `blob[em.start(): em.start() + 400]` around each `eventId` match to find the `eventPage` field. For events with long `bannerUrl`/`squareImage` values, `eventPage` can appear beyond 400 chars (worst case ~480). Fixed by bumping the window to 600. Caused Paris Swing Classic 2025 to be silently missed; with the fix the archive page now finds all 52 events correctly.

- **danceconvention per-couple/per-person scoresheets included as divisions**: some events (e.g. Swing&Snow 2025) store individual Classic Routine couple scoresheets alongside division scoresheets. These per-couple entries have no numeric division ID before the first quoted field, unlike real division entries which always follow the pattern `div_id,"Division Name",...`. The old regex `"([^"]+)",... ` matched both. Fixed by anchoring the regex on the division ID: `\d+,"([^"]+)",...`, so per-couple entries (which start with a quoted name) are never matched. Also added a `if division_name.startswith('/'): continue` guard against spurious matches where a pdf_id gets misread as the division ID.

- **danceconvention Cyrillic round names ignored**: some events (e.g. Cash&Swing 2025) store round names in Russian Cyrillic, e.g. `"JnJ newcomer / Финал"` (Final) and `"JnJ novice / Отбор"` (Qualifier). The `FINALS_IN_NAME` regex only matched Latin "final", so all these rounds were silently skipped (0 finals found). Fixed by adding `|финал` to `FINALS_IN_NAME` and adding `|отбор|полуфинал|четвертьфинал` to `NON_FINALS`.

## Bugs fixed in session 3 (Jan–Jun 2025 re-validation pass, 2026-06-07)

- **transient HTTP timeout silently dropped a whole event**: scoring.dance event 191 (Country Couver 2025, 9 finals) timed out once during January discovery and was lost with only a `WARNING`; a re-fetch succeeded in 0.1s. Fixed by adding a retry loop (3 attempts, exponential backoff) to `RateLimitedClient.get`, catching `httpx.TimeoutException`/`httpx.TransportError`.

- **danceconvention names contained raw HTML entities**: event/division names logged as `Swing&amp;Snow 2025` because the Nuxt blob stores `name:"Swing&amp;Snow 2025"` and `_decode_nuxt` only handles `\uXXXX`. Fixed with `html.unescape()` on `event_name` and `division_name` (scoring.dance/eepro already decode via BeautifulSoup).

- **eepro cross-month date ranges mis-parsed**: `"May 29-June 1, 2025 - Michigan Classic"` didn't match the same-month `Month D-D` regex, fell through to the single-date regex, and was dated `June 1` only — dropping the May 29 start and making it invisible in a May-only window. Fixed by adding a cross-month regex tried before the single-date fallback, with Dec→Jan year-boundary handling. Regression-tested against all eepro date formats.

## Validation status

- **Jan, Feb, Mar, Apr, May, Jun 2025: fully validated.** For each month, every site's per-event finals counts sum to the discovered total and match an independent extraction of the cached list pages; zero `WARNING` lines. Resume at **July 2025**.

## Known source-data caveat (not a script bug)

- **eepro Disco America**: the `eepro.com/results/2025/` listing labels it `June 5-8, 2024` (typo) but its results-page header reads `Disco America - 2025` (slug `discoamerica2025`). The script faithfully parses the listing's `2024` and excludes it from June 2025. Left as-is — auto-correcting the year would need a heuristic that risks corrupting legitimate Dec→Jan crossover events. Decide per project whether Disco America 2025 finals are wanted.

## Resolved "known remaining bug"

- **danceconvention Winter Zouk Fest 2025**: investigated and confirmed the event has no published results (`results:[]` in Nuxt data). Same for Christmas Zouk Championship 2025. 0 finals found is correct behaviour, not a bug.

## Key files

- `scripts/download.py` — the script (all discovery and download logic)
- `data/manifest.jsonl` — manifest of already-downloaded files (may have some entries from earlier test runs)
- `plan.md` — overall project plan for context

## What "correct" looks like

- **scoring.dance**: one entry per division finals page per event. Expect ~5–15 divisions per event, many events per month. The `/enCA/recent` page lists events in reverse-chronological order.
- **eepro.com**: one entry per results page per event. Expect 1–6 pages per event (J&J finals, strictly finals, all-american finals, etc.). Pages named like `jjfinals.html`, `strictlyswing.html`, `allamericanfinals.html`.
- **danceconvention.net**: one PDF per division per event. Expect a handful of divisions per event; events are mostly international/European. Watch for events with 0 finals found — those usually indicate a parsing bug.

## Notes

- The script uses 0.5s per-host rate limiting, so discovery runs take a while even in dry-run mode.
- `logging.warning` lines in the output always warrant investigation.
- The manifest is keyed by URL — already-cached URLs are silently skipped in dry-run output (logged as "Already cached: ...").
