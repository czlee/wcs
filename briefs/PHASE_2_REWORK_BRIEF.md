# Phase 2 Rework Brief — event IDs, division taxonomy, and scoresheet IDs

**For:** a fresh implementing agent. You are picking up a working pipeline and
reworking three things: how events are identified, how divisions are classified,
and how scoresheet IDs are built. Read this whole brief before editing.

---

## 1. Project context

`wcs-judge-divergence` quantifies how much judges on the same panel disagree in
West Coast Swing competition finals. The pipeline:

- **Phase 1 — `scripts/download.py`** (done): discovers and downloads raw final
  scoresheets from three sites into `data/raw/`, with a one-record-per-URL
  manifest at `data/manifest.jsonl` (fields: `url`, `site`, `event_name`,
  `event_start`, `event_end`, `local_path`).
- **Phase 2 — `scripts/extract.py`** (done, being reworked): parses each raw file
  via the vendored parsers in `scripts/parsers/`, validates, normalises
  covariates, and writes one self-contained `data/parsed/{id}.json` per
  scoresheet. Currently produces **418 parsed finals** from 340 manifest entries.

The three sites and how pages map to events:
| Site | Raw format | Page ↔ event |
|---|---|---|
| scoring.dance | HTML (JSON-LD) | many URLs per event (one per division final) |
| eepro.com | HTML tables | **one** URL per event, **many** divisions per page (1:M at parse) |
| danceconvention.net | PDF | many URLs per event (one PDF per division) |

Read `~/.claude/plans/have-a-look-at-refactored-journal.md` (the approved Phase 2
plan) and `scripts/extract.py` before starting — most machinery you need already
exists and must be **reused, not rewritten**.

---

## 2. Hard constraints (do not violate)

- **Vendored parsers are verbatim copies** of `~/who-woulda-won` (only imports
  rewritten). Do **not** edit parser logic in `scripts/parsers/`. All project
  behaviour lives in `extract.py`. See `scripts/parsers/DIVERGENCE.md`.
- **Idempotency**: re-running `extract.py` must not duplicate or churn files. A
  `--force` flag overwrites; default skips already-parsed. IDs must be
  deterministic and stable across runs and across the `--site/--start/--end/--event`
  filters (these select whole events).
- **Hybrid data-quality policy** already implemented — keep it: crash
  (`IntegrityError`) only on genuine parser bugs; skip (with reason, summarised at
  end) on incomplete (`0`/missing placements), too-small fields (`<2` judges /
  `<3` competitors), role-separated/multi-block sheets, and non-finals leaks.
  Don't loosen these into silent passes.

---

## 3. What this rework changes and why

Three coupled changes. Implement them together and re-extract once at the end.

### 3a. Event identity → a real `event_id` (reopen Phase 1)

**Why:** event identity is currently reconstructed downstream from
`(site, event_name, dates)`. That's fragile — `event_name` slugs are lossy and
even encoding-inconsistent (the manifest holds both `Swing&Snow 2025` and
`Swing&amp;Snow 2025` for *one* event), which can split an event or collide two.
A stable event id fixes this and becomes the clean join key for the Phase-4
event-level lookups (region, tier, dance-style/WCS classification).

**Use each site's native event id, namespaced** — do **not** invent a synthetic
key (no allocation state; native ids are stable, unique, traceable):

| Site | site abbr | native id | where it is |
|---|---|---|---|
| scoring.dance | `sd` | numeric event id | in the URL: `/events/228/results/...` |
| eepro.com | `ee` | event slug | in the URL: `/results/swinglebell2025/...` |
| danceconvention.net | `dc` | numeric `eventId` | **only at discovery** — the PDF URL `roundscores/{pdf_id}.pdf` does **not** contain it |

- `event_id = "{site_abbr}-{native_id}"` → `sd-228`, `ee-swinglebell2025`, `dc-301126`.
- **download.py:** capture the native id during discovery (the discovery
  functions already iterate events and know it; `DiscoveredFinal` will need an
  `event_id`/`native_event_id` field) and write `event_id` + `source_event_id`
  into each manifest record. Optionally also emit `data/events.jsonl` (one row per
  event: `event_id`, `site`, `source_event_id`, `event_name`, `event_start`,
  `event_end`) as the dimension table the Phase-4 lookups will join on.
- **Backfill the existing manifest:** sd/ee ids are recoverable from the stored
  URL (regex); **dc must be re-derived by re-running dc discovery** (cheap — list
  page cached, no re-downloads) to rebuild a `pdf_url → event_id` map. Provide a
  one-time migration that adds `event_id`/`source_event_id` to every existing
  manifest record.
- **The danceconvention name-encoding split must collapse:** records for one DC
  event under differently-encoded names must share one `event_id`. The native id
  gives this for free.

### 3b. Division taxonomy (covariate fields) — corrected model

Normalise into these fields (keyword-matched on the **isolated division blob** —
see `isolate_division_blob` in `extract.py`; keep matching off the blob, not the
full `competition_name`, to avoid event-name contamination):

- **`division_level`** — a single flat field; skill rungs and age categories are
  peers (Masters/Sophisticated/Junior are *levels*, not comp types — confirmed by
  the user; it's a bit odd but that's how they work in practice). Category wins
  when both appear (`Masters Novice` → Masters; rare). Starting value set:
  Newcomer, Novice, Intermediate, Advanced, All-Star, Champions, Open, Masters,
  Sophisticated, Junior, Invitational, All-American, Unknown. **Pro-Am is NOT a
  level** (see below); for a pro-am division, `division_level` is the *amateur's*
  skill rung, or Unknown if the name carries none.
- **`dance_format`** — now **includes pro-am as part of the format axis** (user
  decision: a Pro-Am J&J is a fundamentally different competition from a J&J —
  the pros aren't assessed — so the two are never comparable and must not share a
  format). So format = base dance (J&J / Strictly / Classic) × pro-am-ness
  (none / pro-am-leader / pro-am-follower / pro-am-unspecified). Role markers seen
  in data: `(AmL)`/`(AmF)`, trailing ` L final`/` F final`, `LEADER`/`FOLLOWER`
  prefixes. Plus `Unknown`.
- Keep `num_judges`, `num_competitors`, `event_date` (Saturday rule), the verbatim
  `competition_name`, etc., as they are now.

### 3c. Scoresheet ID scheme

- `id = "{event_slug}_{event_id}_{div_token}"`, e.g.
  `swingcouver_2025_sd-228_str_chp` (abbreviated) or, for an unusual division,
  `swingcouver_2025_sd-228_rising_star_routines` (raw fallback).
  - `event_slug` = readable slug of `event_name` (decoration only).
  - `event_id` (e.g. `sd-228`) carries **global uniqueness** — so the lossy
    event_slug never needs to be unique and all the old slug-collision/salting
    machinery (`event_id_prefixes`) is **deleted**.
  - `div_token` — see below.
- **`div_token`**: the abbreviated code **`{format}_{level}`** (format first), e.g.
  `jnj_nov`, `str_new`, `pamljnj_int`, `pamjnj_adv` — **only for comp-types/levels
  in the agreed standard set**; otherwise the **raw division slug**. Strip round
  words (`final`/`finals`/Cyrillic `финал`) from both — they're all finals.

### Abbreviation map (starting point — FINALISED at the §4 checkpoint)

The `format` code is a **single atomic token with no internal underscore**, so the
`{format}_{level}` id token always has exactly one separator. Pro-am is folded into
the format and **keeps its base dance** (a pro-am Strictly ≠ a pro-am J&J):

| `dance_format` | code |
|---|---|
| J&J | `jnj` |
| Strictly | `str` |
| Classic | `cla` |
| Pro-Am J&J (no role split) | `pamjnj` |
| Pro-Am J&J, amateur Leader | `pamljnj` |
| Pro-Am J&J, amateur Follower | `pamfjnj` |
| Pro-Am Strictly (—/Leader/Follower) | `pamstr` / `pamlstr` / `pamfstr` |
| Unknown | raw fallback |

| `division_level` | code |
|---|---|
| Newcomer | `new` |
| Novice | `nov` |
| Intermediate | `int` |
| Advanced | `adv` |
| All-Star | `als` |
| Champions | `chp` |
| Open | `opn` |
| Invitational | `inv` |
| All-American / All-European / All-Australian / … (all the same thing) | `all` |
| Sophisticated | `sop` |
| Masters | `mas` |
| Junior | `jnr` |
| Unknown | raw fallback |

Pro-am role markers seen in data, for detection: `(AmL)`/`(AmF)`, trailing
` L final`/` F final`, `LEADER`/`FOLLOWER` prefixes. Levels/formats not in this map
(novelty, non-WCS, deep sub-tiers like Hustle "Legends/Open") get the **raw slug**,
not a bespoke code — the §4 inventory is where the user decides what's standard.
- The abbreviate-or-raw choice is **deterministic per division** (keyed on whether
  its classification is in the standard set + the abbreviation map — *not* on its
  siblings), so there's no sibling-dependence instability.
- Residual collisions (two divisions in one event producing the same token, e.g.
  NJ Hustle `Intermediate Legends` vs `Intermediate Open` → both `pamfjnj_int`)
  get a positional `_2` suffix. These are intra-event, so the event filters never
  split them and the suffix stays stable. (This is the existing `make_id`
  behaviour; keep it.)

---

## 4. ★ Deliverable + checkpoint: division/comp-type inventory (do this first)

Before finalising any abbreviation map, **produce an inventory for the user to
review, and stop.** Extend the existing `extract.py --dump-divisions` mode.

The inventory must list, across all manifest entries:
- every distinct **isolated division blob**, with its **frequency** (how many
  scoresheets),
- its first-pass classification: proposed `division_level`, `dance_format`
  (incl. pro-am + role), and proposed `div_token`,
- a clear flag for anything Unknown / unmatched / unusual.

Group/sort so the user can see at a glance which comp-types and levels are
**common** (worth a standard abbreviation) vs **unusual/novelty** (should fall
back to the raw slug — do **not** invent bespoke abbreviations for one-offs).

**Then pause and ask the user to:**
1. confirm/adjust the abbreviation map (level codes, format/pro-am codes, role
   markers), and
2. mark which comp-types are "standard" (abbreviated) vs "raw fallback".

Only after that sign-off, finalise normalisation + IDs and re-extract.

Known messy cases to surface in the inventory (from prior analysis): Pro-Am with
`(AmL)/(AmF)` and with `Legends/Open` sub-tiers; Masters with `50+`/age
qualifiers; `Switch`/`Switchly`/role-rotation formats; novelty/event-specific
names (`Avalanche J&J`, `WCS 101`, `JackPot`, `History J&J`); non-WCS dances
(`Line Dance`, `Country Two-Step`, Bachata); regional `All-American` variants
(`All Australian`, `All Korean`, …); source typos (`Invitaional`).

---

## 5. Tasks (suggested order)

1. **Inventory deliverable** (§4) → checkpoint with user.
2. **download.py + manifest**: native `event_id` capture, manifest migration
   (sd/ee from URL, dc via discovery re-run), optional `events.jsonl`.
3. **extract.py taxonomy**: corrected `division_level`, pro-am-aware
   `dance_format`, using the user-approved abbreviation map.
4. **extract.py IDs**: new `id` scheme (`event_slug_event_id_div_token`), delete
   `event_id_prefixes` salting, keep positional intra-event suffix; carry
   `event_id`/`source_event_id` into each parsed JSON.
5. **Re-extract** (`--force`) and verify (§6).

---

## 6. Verification

- `extract.py` runs clean (no `IntegrityError` crash); skip summary only contains
  expected categories.
- Counts: ~418 parsed files (± any new standard-set decisions); eepro 1:M
  expansion intact.
- **Event id integrity:** every parsed file has `event_id`; the DC Swing&Snow
  event is no longer split across two ids; no two distinct events share an
  `event_id`.
- **ID stability under filters:** a filtered run (`--site`, `--start/--end`,
  `--event`) produces byte-identical ids to the full run for the overlapping
  scoresheets; re-run is idempotent (0 written) and `--force` rewrites in place
  with no duplicates.
- Spot-check per site: rankings are clean `1..N` permutations; pro-am divisions
  classify with the right level + role; `div_token` matches the agreed map or
  falls back to raw for unusual divisions.
- Dump the final division→token mapping and eyeball for collapses/leaks before
  declaring done.

---

## 7. Gotchas (learned the hard way)

- **Per-site division position in `competition_name`** differs: scoring.dance &
  eepro put the division *last*; danceconvention puts the event *last*
  (`Division - Finals - Event`). `isolate_division_blob` already handles this —
  reuse it.
- **eepro is 1:M**: enumerate divisions via `EeproParser().get_division_names()`;
  one parsed file per division. eepro divisions have **no native per-division id**.
- **Role-separated sheets** (leaders+followers in one table → ranks are k blocks
  of `1..m`) are detected and skipped by `block_structure`/`validate`. Keep that.
- **Numeric prelims** that leak (e.g. eepro "All American Prelims") are caught by
  `looks_like_non_finals` on the competition name. Keep that.
- One danceconvention PDF (`roundscores/300341375.pdf`, Swing&Snow) is a Russian
  numeric-callback prelims the parser can't table-parse → skipped as a parse
  error. Correct to skip; don't chase it.
- Keep covariate keyword-matching on the **isolated division blob**, not the full
  `competition_name` (a real eepro event is named `Novice Invitational`, which
  would otherwise inject a false "Novice").
