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

**Goal:** Build a local cache of as many final scoresheets as possible, with metadata.

**Approach:** Write `scripts/collect.py`, adapting the discovery functions from `check_new_scoresheets.py`:
- Accepts a `--site` argument (scoring.dance / eepro / danceconvention); defaults to all three. In practice, run one process per site in parallel.
- Sweep a date range (start: ~2020-01-01, end: today) for all three sites
- For each discovered final, download raw content and save to `data/raw/`; skip if already cached
- Add polite rate limiting (e.g. 0.5–1 s between requests per host) to avoid being blocked
- Save a manifest at `data/manifest.jsonl` with one record per downloaded file:
  - `url`, `site`, `event_name`, `division_raw`, `event_date`, `local_path`

**Filtering:** Only keep finals (already handled by discovery code). Skip prelims, semis, quarters.

**WCS-only filter:** The three sites are primarily WCS but may include other styles (Lindy Hop, Hustle, etc.). Filter to WCS-only before analysis. Implementation TBD — may require an agent to classify events by name, since automated keyword matching is unreliable.

**Error handling:** Parse errors or unexpected content during collection should log a warning and skip — don't abort the whole run.

**Note:** Watch out for the same scoresheet being discoverable under multiple URLs (e.g. a PDF linked from two event pages). The URL-based cache handles most cases; verify with a spot-check.

**Volume estimate:** Likely hundreds to low thousands of finals per year across all three sites.

---

## Phase 2: Extraction and Validation

**Goal:** Parse every raw file into a single standardised format, run data quality checks, and produce a clean dataset ready for metric computation.

**Approach:** Write `scripts/extract.py`:
- For each entry in `data/manifest.jsonl`, load the raw file and run it through the appropriate parser (same import pattern as `check_new_scoresheets.py`)
- Skip if a parsed file for this entry already exists (`data/parsed/{id}.json`) — re-run is incremental
- Assign each scoresheet a **unique ID**: a human-readable slug (`{site}_{event_slug}_{division_slug}`) with a numeric suffix added if there is a collision
- Write to `data/parsed/{id}.json`; the slug/ID is for convenience only — all critical information must be in the file contents:
  - `id`, `url`, `site`, `event_name`, `division_raw`, `event_date`, `division_level`, `dance_format`, `num_judges`, `num_competitors`, `competitors` (list), `judges` (list), `rankings` (judge → competitor → rank)
- **Data quality checks** — these run after parsing; raise an exception and crash if any fail (a violation here indicates a parser bug, not bad source data):
  - Each judge's ranking is a permutation of the competitors (no missing entries, no duplicate ranks, no rank collisions)
  - Number of judges ≥ 2; number of competitors ≥ 3
  - Rankings dict keys match the judges list exactly
- Normalised covariate fields assigned at this stage:
  - `division_level` (Novice / Intermediate / Advanced / All-Star / Open / Champions / Masters / Unknown) — keyword match on `division_raw`
  - `dance_format` (J&J / Classic / Strictly / Unknown) — keyword match on `division_raw`
  - `num_judges`, `num_competitors` — computed directly

**Design note:** Additional characteristics that require manual lookup tables (geographic region, competition tier) are kept in separate files in `lookups/` and joined at analysis time, not baked into the parsed files. The `id` field is the join key. This keeps the pipeline stages independent and the lookup tables easy to edit without re-extracting.

This stage acts as the single interface between raw data and all downstream work. If the format of a source changes or a new parser is added, only this script needs updating.

---

## Phase 3: Divergence Metrics

**Script:** `scripts/compute_metrics.py` — reads files from `data/parsed/`, writes `results/metrics.csv` (one row per scoresheet, metrics + covariates as columns).

**Metrics to be decided in a separate investigation.** Candidates to evaluate:
- Kendall's W (coefficient of concordance)
- Mean pairwise Kendall's tau
- Top-N agreement rate
- Mean absolute rank deviation across judges

The choice of metric(s) warrants its own focused session before implementation.

---

## Phase 4: Covariates / Characteristics to Compare

The normalised covariate fields (`division_level`, `dance_format`, `num_judges`, `num_competitors`) are already assigned in Phase 2. Additional covariates:

### Derivable from metadata
| Covariate | Source |
|---|---|
| **Data source/site** | From manifest |
| **Year** | From `event_date` |
| **Event** | From `event_name` — can study whether some events are consistently higher/lower divergence |

### Requiring manual mapping
| Covariate | Notes |
|---|---|
| **Geographic region** | Infer from event name (e.g. "NZO" = New Zealand Open, "USDC" = US Dance Championships); build a lookup table as a small JSON file |
| **Competition tier** (major nationals vs. regional) | Manual tagging based on known competition list |

### Possible interaction effects to explore
- Does divergence scale with division level? (Hypothesis: higher levels may have more consensus because judges agree on quality, or alternatively more divergence because top-level differences are subtle)
- Does panel size (5 vs 7 vs 9) affect divergence? (Larger panels may or may not have more variance)
- Does field size matter? (Closer fields may produce more divergence)

---

## Phase 5: Analysis

**Output:** A written write-up (not a formal paper) summarising findings.

Primary mode is visual: if a pattern isn't obvious on a plot, it isn't interesting. Statistical tests can be used to confirm what's already visible, not to go fishing.

1. **Descriptive stats:** Distribution of divergence metric(s) across the full dataset
2. **Visualization:**
   - Box plots / violin plots by division level
   - Scatter plot of divergence vs. field size
   - Scatter plot of divergence vs. panel size
   - Any other obvious cuts (year, site, competition tier)
3. **Confirmation:** For patterns that look visually clear, a simple statistical test (e.g. Kruskal-Wallis or Spearman correlation) to check it isn't noise

Tools: Python with `pandas`, `scipy`, `matplotlib`/`seaborn`. Use a Jupyter notebook for the exploratory analysis phase.

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
  scripts/
    collect.py                  # Phase 1: discover and download scoresheets
    extract.py                  # Phase 2: parse raw files, validate, normalise covariates
    compute_metrics.py          # Phase 3: compute divergence metrics → results/metrics.csv
    analyze.ipynb               # Phase 5: exploratory analysis and visualisations
  lookups/
    regions.json                # manual mapping: event name → geographic region
    tiers.json                  # manual mapping: event name → competition tier
  results/
    metrics.csv                 # output of compute_metrics.py
```

---

## Implementation Notes

- All Python scripts should use `poetry` from the `~/who-woulda-won` directory for imports (or set up a `pyproject.toml` here that depends on the same packages: `httpx`, `beautifulsoup4`, `pdfplumber`, `scipy`, `pandas`, `matplotlib`)
- The parsers live in `~/who-woulda-won/core/parsers/`; the simplest approach is to `sys.path.insert` the parent and import them directly, as `check_new_scoresheets.py` already does
- Rate limiting: use `httpx` with a custom transport or just `time.sleep(0.5)` between requests
- Caching: save raw bytes to `data/raw/` with a filename derived from the URL (e.g. MD5 hash or slugified URL); skip download if file exists
- Handle `PrelimsError` (raised by parsers for non-finals rounds) gracefully in `collect.py`; the extraction stage should never see prelims data

---

## Open Questions / Decisions

1. **How far back should data collection go?** danceconvention.net has data from at least 2020; scoring.dance and eepro.com may have less history. Start with 2022–present to keep scope manageable.
2. **WCS-only filter implementation:** Filtering is necessary but automated keyword matching on event/division names is unreliable. Likely needs a manual or agent-assisted pass over the collected event list.
3. **Minimum panel/field size?** Scoresheets with very few judges or competitors may not be meaningful. Define inclusion criteria (e.g. ≥ 5 judges, ≥ 6 competitors) when implementing compute_metrics.py.
4. **Judge identity:** Judges are identified by initials or names; we won't try to track individual judges across events (too complex), so analysis will be at the panel level, not per-judge.
