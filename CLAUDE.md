# WCS Judge Divergence — Project Guide

**Goal:** Quantify how much judges on the same panel disagree in WCS competition finals, and find what predicts higher or lower divergence (division level, panel size, field size, etc.).

See `plan.md` for the full project plan and open questions, and `ideas.md` for unplanned ideas (explorer filters, x-axis options, data to collect).

---

## Phase Status

| Phase | Script | Status |
|---|---|---|
| 1 — Download | `scripts/download.py` | ✅ Complete |
| 2 — Extract | `scripts/extract.py` | ✅ Complete |
| 3 — Metrics | `scripts/compute_metrics.py` | ✅ Complete |
| 4 — Covariates | (lookup tables + join at analysis time) | ⬜ Not started |
| 5 — Analysis | `notebooks/analyze.ipynb` | ⬜ Not started |

Debugging history for Phases 1 and 2 is in `briefs/`.

---

## Results site (`site/`)

A static SvelteKit site presenting the `explore_metrics.ipynb` bar and box charts (J&J and Strictly, six levels, 12 metrics), with the method and limitations inline and every metric worked through on any scoresheet. Deployed by `.github/workflows/pages.yml` to **https://czlee.nz/wcs/judge-divergence/** (this assumes the GitHub repo is named `wcs`).

- **Data:** `scripts/export_site_data.py` writes `site/src/lib/data/{sheets.json,export.json}` from `data/metrics.csv` + `data/parsed/` + `lookups/regions.json`. The output is **committed**, because CI can't run the pipeline. Re-run it after recomputing metrics.
- **JS port of the metrics:** `site/src/lib/metrics.js` must reproduce `compute_metrics.py`. `npm run check:metrics` (also run in CI) compares every value; if you change a metric in Python, change it in JS too.
- **Filters:** finalists (a two-sided slider) and judges (buttons), defined in `site/src/lib/dimensions.js` (browser-safe; bin ids are URL values, so keep them stable), drawn by `FilterBar.svelte` on the explorer and `/sheets/`. Chart axes come from the unfiltered rows (the bar axis grows if it must, ignoring grey cells); cells under `MIN_CELL` (`stats.js`) are grey, without an interval or a box.
- **Highlighted scoresheet:** the explorer's `SheetPicker.svelte` (searched with `lib/fuzzy.js`, an IDE-style word-aware matcher) sets the scoresheet ringed in the box plot and worked through in the calculation dialog; until one is chosen it's random.
- **Dialogs (design assumption):** the explorer and its dialogs are the site; the long-form and `/sheet/<id>/` pages are still there but to be deprecated, so nothing new should depend on them, and the explorer (and the footer) links to none of them or to `/sheets/`. `ExplorePage.svelte` has one `dialog` state (`working`, `profile`, `limitations`, `about`), so dialogs can lead to each other. `working` (title is a metric dropdown) shows one metric's `Standing.svelte` (value and percentile) and working; `profile` (the "details" link) shows the scoresheet's overview and `MetricsTable.svelte` (shared with the `/sheet/<id>/` page). The `Worked*.svelte` text must stand alone for one metric when given `focus`: don't refer to metrics the reader can't see. Percentiles (`percentiles` in `server/data.js`, worded in `lib/percentiles.js`) come with each scoresheet's `data.json`.
- **URLs:** `lib/view.js` has the explorer's URL parameters (`metric`, `sheet`, `dialog`, and the filters'), which must stay stable. `sheet` is there only once a scoresheet is chosen or a dialog about it is opened. Opening a dialog adds a history entry (so Back goes back through them) and everything else rewrites the current one, through `goto(…, {shallow: true})`; × goes back past every dialog (`page.state.depth`) and keeps the current view. Back and Forward are handled by `popstate`, always from `location`, because SvelteKit's `afterNavigate` doesn't run for all of them.
- **No legacy:** the site is published but unannounced, so there's no backwards compatibility to keep, and no deprecated API should be used (check the installed version's types: Kit 3 deprecates `pushState`/`replaceState` and `json()`).
- **Routes:** `/` and `/strictly/` = the explorer (`ExplorePage.svelte`: one metric at a time, a full-screen app on desktop ≥ 900×600, random non-`hidden` metric on load); `/long-form/` and `/long-form/strictly/` = every metric on one page (`FormatPage.svelte`); `/sheets/` (browse/filter), `/sheet/<id>/` (prerendered per scoresheet at build time, not committed), `/sheet/<id>/data.json` (loads a scoresheet into the explorer's dialogs). `FORMATS` in `levels.js` has `path` (explorer) and `longPath`. The explorer's narrow-screen layout is a placeholder, to be redesigned for mobile.
- **Provisional/deferred:** the CI method (`site/src/lib/stats.js` `meanCI`, currently ±1.96·SE), the limitations wording (`site/src/lib/components/Limitations.svelte`), and the top-N treatment: the site shows top-3 only (the @5 columns stay in `metrics.csv`), charts it for finals of n ≥ 6 only (`minN` in `site/src/lib/families.js`, applied in `server/data.js` `chartRows`), and defaults to the naive chance-corrected `*_cc` columns (`topn_chance` in `compute_metrics.py`). `site/src/lib/config.js` `DRAFT` is true (draft banner + noindex) until launch.
- **Local:** `cd site && npm install && npm run dev`. `vite preview` 500s on the base-path root (a SvelteKit preview bug), so to test the build, serve `build/` as `wcs/judge-divergence/` with any static server.

---

## Environment

```bash
python -m venv venv          # venv/, not .venv/
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` already includes `pandas`, `plotly`, `jupyterlab`, `scipy`. No additional packages needed for Phase 5.

---

## File Layout

```
data/
  raw/                  # Phase 1: cached raw files (named by MD5 of URL)
  manifest.jsonl        # Phase 1: one record per downloaded file
  events.jsonl          # Phase 1: one record per discovered event (namespaced event_id)
  parsed/               # Phase 2: one JSON per scoresheet ({id}.json)
  metrics.csv           # Phase 3: one row of divergence metrics per scoresheet (compute_metrics.py)
  division-inventory.html  # generated by inventory.py
  extract-skips.html       # generated by extract.py (skipped/errored files report)
scripts/
  download.py           # Phase 1
  extract.py            # Phase 2
  inventory.py          # helper: renders data/division-inventory.html
  export_site_data.py   # writes site/src/lib/data/ for the results site
  parsers/              # vendored parsers (scoring_dance, eepro, danceconvention)
notebooks/
  division_stats.ipynb    # exploratory: field and panel size distributions by division
  explore_metrics.ipynb   # exploratory: divergence metrics by division level
  analyze.ipynb           # Phase 5: analysis notebook (when implemented)
briefs/                 # extended history/debugging notes per phase
lookups/                # (planned) manual mapping tables joined at analysis time
```

---

## Parsers

Parsers are **vendored** in `scripts/parsers/` — do not import from `~/who-woulda-won`.

`extract.py` makes them importable with:
```python
sys.path.insert(0, str(Path(__file__).parent))  # adds scripts/ to path
from parsers import detect_parser, ...
from parsers.base import PrelimsError
```

The three parsers: `scoring_dance`, `eepro`, `danceconvention`.

---

## Key Data Relationships

- **manifest.jsonl → parsed/**: 1:M. A single eepro page can contain multiple divisions, producing multiple `data/parsed/{id}.json` files from one manifest entry.
- **Parsed file fields:** `id`, `url`, `raw_file`, `site`, `event_name`, `event_id`, `source_event_id`, `event_start`, `event_end`, `event_date`, `competition_name`, `division_level`, `dance_format`, `num_judges`, `num_competitors`, `judges`, `competitors`, `rankings`.
- **`event_date`:** normalised canonical date (the Saturday of a weekend event, or the actual competition day otherwise). Computed in Phase 2.
- **`division_level`** and **`dance_format`** are keyword-matched from `competition_name` in `extract.py`. The keyword maps are a starting point — run `inventory.py` to review unmatched divisions before trusting the output.

---

## Non-WCS Filtering

`download.py` filters out definitively non-WCS divisions at discovery time using `NON_WCS_STYLE_RE` (salsa, bachata, zouk, lindy, hustle, country, silc, etc.). This is a best-effort filter — a manual or agent-assisted pass over the event list may still be needed before analysis (see plan.md open question 2).
