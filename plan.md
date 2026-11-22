# WCS Judge Divergence Study — Project Plan

**Goal:** Quantify how much judges on the same panel disagree in WCS competition finals, and find what predicts higher or lower divergence (division level, panel size, field size, etc.).

> This plan is a rough guide. Agents implementing individual phases should use their judgement and diverge from it where appropriate.

---

## Existing infrastructure (~/who-woulda-won)

Three data sources already have parsers and discovery code:

| Site | Format | Discovery mechanism |
|---|---|---|
| `scoring.dance` | HTML (JSON-LD) | `/enCA/recent` listing → per-event results page |
| `eepro.com` | HTML table | `/results/{year}/` listing → per-event finals pages |
| `danceconvention.net` | PDF | `/eventdirector/en/eventsarchive/{year}` → per-event results page |

`scripts/check_new_scoresheets.py` already has full discovery logic for all three sites, including filtering for finals vs. prelims/semis. The `Scoresheet` model provides: `competition_name`, `competitors`, `judges`, `rankings` (judge → competitor → rank).

---

## Phase 1: Data Collection

**Status:** ✅ Complete — `scripts/download.py` implemented; discovery validated month-by-month against all three sites' list pages for Jan–Jun 2025 (Jul–Dec not yet validated).

**Goal:** Build a local cache of as many final scoresheets as possible, with metadata.

**Approach:** Write `scripts/download.py`, adapting the discovery functions from `check_new_scoresheets.py`:
- Accepts a `--site` argument (scoring.dance / eepro / danceconvention); defaults to all three. In practice, run one process per site in parallel.
- Sweep a date range (default: calendar year 2025; extend later as needed) for all three sites
- For each discovered final, download raw content and save to `data/raw/`; skip if already cached
- Add polite rate limiting (e.g. 0.5–1 s between requests per host) to avoid being blocked
- Save a manifest at `data/manifest.jsonl` with **one record per downloaded file** (keyed by URL):
  - `url`, `site`, `event_name`, `event_start`, `event_end`, `local_path`
  - `event_start` / `event_end` are raw dates from the discovery source. A normalised `event_date` is intentionally not computed here — that logic (e.g. use the Saturday of a weekend event) belongs in Phase 2.
  - No division fields — division extraction is Phase 2's responsibility. For eepro.com pages that contain multiple divisions, Phase 2 produces multiple parsed outputs from one manifest entry (1:M).

**Filtering:** Only keep finals (already handled by discovery code). Skip prelims, semis, quarters.

**WCS-only filter:** The three sites are primarily WCS but may include other styles (Lindy Hop, Hustle, etc.). Filter to WCS-only before analysis. Implementation TBD — may require an agent to classify events by name, since automated keyword matching is unreliable.

**Error handling:** Parse errors or unexpected content during collection should log a warning and skip — don't abort the whole run.

**Note:** Watch out for the same scoresheet being discoverable under multiple URLs (e.g. a PDF linked from two event pages). The URL-based cache handles most cases; verify with a spot-check.

**Volume estimate:** Likely hundreds to low thousands of finals per year across all three sites.

---

## Phase 2: Extraction and Validation

**Status:** ✅ Complete — `scripts/extract.py` implemented and reworked; 1459 parsed finals
in `data/parsed/`; each file carries `event_id`/`source_event_id` from the manifest.
See `briefs/phase-2-rework-brief.md` for full history.

**Goal:** Parse every raw file into a single standardised format, run data quality checks, and produce a clean dataset ready for metric computation.

**Approach:** Write `scripts/extract.py`:
- For each entry in `data/manifest.jsonl`, load the raw file and run it through the appropriate parser (same import pattern as `check_new_scoresheets.py`)
- Skip if a parsed file for this entry already exists (`data/parsed/{id}.json`) — re-run is incremental
- Assign each scoresheet a **unique ID**: a human-readable slug (`{site}_{event_slug}_{division_slug}`) with a numeric suffix added if there is a collision
- Write to `data/parsed/{id}.json`; the slug/ID is for convenience only — all critical information must be in the file contents:
  - `id`, `url`, `raw_file`, `site`, `event_name`, `event_id`, `source_event_id`, `event_start`, `event_end`, `event_date`, `competition_name`, `division_level`, `dance_format`, `num_judges`, `num_competitors`, `judges` (list), `competitors` (list), `rankings` (judge → competitor → rank)
  - `event_start` / `event_end` carried through from the manifest; `event_date` is the normalised canonical date derived here (the Saturday of a weekend event, or the actual competition day for non-weekend events)
- **Data quality checks:**
  - Integrity checks (run after parsing) **raise and crash** if they fail — a violation indicates a parser bug, not bad source data: each judge's ranking is a permutation of the competitors (no missing entries, no duplicate ranks, no rank collisions); the rankings dict keys match the judges list exactly
  - Size thresholds are **skip conditions** (logged to the skips report, not crashes): scoresheets with fewer than 3 judges or fewer than 5 competitors are skipped
- Normalised covariate fields assigned at this stage:
  - `division_level` — keyword match on `competition_name`; one of Masters / Sophisticated / Junior / Invitational / Champions / All-Star / All-American / Advanced / Intermediate / Novice / Newcomer / Open, or `null` if unmatched (see `LEVEL_PATTERNS` in `extract.py`)
  - `dance_format` — keyword match on `competition_name`; Jack & Jill / Strictly / Classic / Routine / Showcase / Rising Star / Switch (J&J or Strictly) / Pro-Am (J&J or Strictly, optionally Leader/Follower), or `null` if unmatched
  - `num_judges`, `num_competitors` — computed directly

**Design note:** Additional characteristics that require manual lookup tables (geographic region, competition tier) are kept in separate files in `lookups/` and joined at analysis time, not baked into the parsed files. The `id` field is the join key. This keeps the pipeline stages independent and the lookup tables easy to edit without re-extracting.

This stage acts as the single interface between raw data and all downstream work. If the format of a source changes or a new parser is added, only this script needs updating.

---

## Phase 3: Divergence Metrics

**Status:** ⬜ Not started.

**Script:** `scripts/compute_metrics.py` — reads files from `data/parsed/`, writes `data/metrics.csv` (one row per scoresheet, metrics + covariates as columns).

**Metrics are specified in `briefs/phase-3-implementation-brief.md`** (informed by
`briefs/judge-divergence-metrics-research.md`), which supersedes this section. Candidates
originally evaluated:
- Kendall's W (coefficient of concordance)
- Mean pairwise Kendall's tau
- Top-N agreement rate
- Mean absolute rank deviation across judges

That investigation is complete; see the brief above for the final metric set and the
rationale for storing raw values with size-correction deferred to Phases 4/5.

---

## Phase 4: Covariates / Characteristics to Compare

**Status:** ⬜ Not started.

The normalised covariate fields (`division_level`, `dance_format`, `num_judges`, `num_competitors`) are already assigned in Phase 2. Covariates derivable from metadata (`site`, `year`, `event_name`) can be joined in at analysis time directly. Two additional covariates require separate work:

### Task 4A: Geographic region lookup

Build `lookups/regions.json` — a manual mapping from event name to geographic region (e.g. "NZO" → "New Zealand", "USDC" → "United States"). Joined to metrics at analysis time using `event_name` or `event_id` as key.

**To start:** extract the list of distinct event names/IDs from `data/parsed/` to see what needs mapping.

### Task 4B: Competition format (stretch)

Whether the final was **spotlights**, **cluster spotlights**, or **all-skates** would be highly valuable for explaining divergence differences. However, this information is not on any of the source sites and would require manual research or crowdsourcing per event. Treat as a stretch covariate — valuable if filled in, but not blocking analysis.

If pursued: build `lookups/formats.json` with the same join key as regions.

### Possible interaction effects to explore
- Does divergence scale with division level? (Hypothesis: higher levels may have more consensus because judges agree on quality, or alternatively more divergence because top-level differences are subtle)
- Does panel size (5 vs 7 vs 9) affect divergence? (Larger panels may or may not have more variance)
- Does field size matter? (Closer fields may produce more divergence)
- Does competition format (spotlights vs. all-skates) affect divergence?

---

## Phase 5: Analysis

**Status:** ⬜ Not started.

**Output:** A written write-up (not a formal paper) summarising findings.

Primary mode is visual: if a pattern isn't obvious on a plot, it isn't interesting. Statistical tests can be used to confirm what's already visible, not to go fishing.

1. **Descriptive stats:** Distribution of divergence metric(s) across the full dataset
2. **Visualization:**
   - Box plots / violin plots by division level
   - Scatter plot of divergence vs. field size
   - Scatter plot of divergence vs. panel size
   - Any other obvious cuts (year, site, competition tier)
3. **Confirmation:** For patterns that look visually clear, a simple statistical test (e.g. Kruskal-Wallis or Spearman correlation) to check it isn't noise

Tools: Python with `pandas`, `scipy`, `plotly`. Use a Jupyter notebook for the exploratory analysis phase.

---

## Results site: filters

**Status:** implemented in `site/` (explorer and scoresheet list).

Field size changes the metrics directly (a ranking of 5 has far less room to disagree than a ranking of 15, and top-N chance agreement depends on n), and levels differ in field size. Filtering shows how much of the difference between levels remains among finals of similar size.

- **Dimension registry** (`site/src/lib/dimensions.js`): one definition per dimension (id, label, accessor, ordered bins). Meant to serve x-axis grouping and colour-by too, if those happen (`ideas.md`). No exported data was needed: chart rows already carry the judge and competitor counts.
- **Finalists:** 5 / 6–7 / 8–10 / 11–13 / 14+, which hold 236 / 310 / 974 / 628 / 378 of the 2,526 sheets (J&J and Strictly, exported 2026-11-22). Finals of 5 are on their own because they're common, their metrics differ from 6–7, and the top-3 charts leave them out.
- **Judges:** 5 / 7 / 9. The 11 finals with other panel sizes show only when no judges filter is on.
- Finalists is a two-sided slider from 5 to 16+ (its bins are kept for grouping and colour-by); judges are buttons, several at once. The state is in the URL (`?finalists=8-10&judges=5,7`; `14-up` for open-ended).
- Grey cells don't count towards the bar chart's axis, and are clipped if they don't fit.
- Cells under 10 scoresheets are grey, without an interval or a box (the points still show). Axes come from the unfiltered data, so views can be compared.
- Percentiles on a scoresheet's page compare it with all finals of its format, at every level, and ignore filters.

---

## Project File Structure

```
wcs-judge-divergence/
  plan.md                       # this file
  data/
    raw/                        # Phase 1: cached raw scoresheet files (named by URL hash or slug)
    manifest.jsonl              # Phase 1: one record per downloaded file (url, site, event, etc.)
    parsed/                     # Phase 2: one JSON file per scoresheet, human-readable slug names
      scoring_dance_budafest2025_novice.json
      eepro_usdc2024_intermediate.json
      ...
    metrics.csv                 # Phase 3: output of compute_metrics.py (one row per scoresheet)
  scripts/
    download.py                 # Phase 1: discover and download scoresheets
    extract.py                  # Phase 2: parse raw files, validate, normalise covariates
    compute_metrics.py          # Phase 3: compute divergence metrics → data/metrics.csv
    analyze.ipynb               # Phase 5: exploratory analysis and visualisations
  lookups/
    regions.json                # manual mapping: event name → geographic region
    formats.json                # manual mapping: event name → competition format (spotlights/cluster/all-skates)
```

---

## Implementation Notes

- Python environment: plain `venv` (named `venv/`, not `.venv/`) with `requirements.txt`. Create with `python -m venv venv && pip install -r requirements.txt`. Packages needed across all phases: `httpx`, `beautifulsoup4`, `lxml`, `pdfplumber`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `jupyter`.
- The parsers live in `~/who-woulda-won/core/parsers/`; the simplest approach is to `sys.path.insert` the parent and import them directly, as `check_new_scoresheets.py` already does
- Rate limiting: use `httpx` with a custom transport or just `time.sleep(0.5)` between requests
- Caching: save raw bytes to `data/raw/` with a filename derived from the URL (e.g. MD5 hash or slugified URL); skip download if file exists
- Phase 1 (`download.py`) filters out prelims/semis/quarters at discovery. As a safety net, `extract.py` should still handle `PrelimsError` (raised by parsers for non-finals rounds) gracefully, so the parsed dataset never contains prelims data

---

## Open Questions / Decisions

1. **How far back should data collection go?** ~~Start with 2022–present.~~ **Decision: start with calendar year 2025, extend to earlier years later once the pipeline is validated.**
2. **WCS-only filter implementation:** Filtering is necessary but automated keyword matching on event/division names is unreliable. Likely needs a manual or agent-assisted pass over the collected event list.
3. **Minimum panel/field size?** Scoresheets with very few judges or competitors may not be meaningful. Define inclusion criteria (e.g. ≥ 5 judges, ≥ 6 competitors) when implementing compute_metrics.py.
4. **Judge identity:** Judges are identified by initials or names; we won't try to track individual judges across events (too complex), so analysis will be at the panel level, not per-judge.
