# Phase 2 Rework Brief — event IDs, division taxonomy, and scoresheet IDs

**For:** a fresh implementing agent. You are picking up a working pipeline and
completing the remaining implementation. Read this whole brief before editing.

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
  scoresheet. Currently produces ~418 parsed finals from 340 manifest entries
  (manifest has since grown to 692 entries).

The three sites and how pages map to events:
| Site | Raw format | Page ↔ event |
|---|---|---|
| scoring.dance | HTML (JSON-LD) | many URLs per event (one per division final) |
| eepro.com | HTML tables | **one** URL per event, **many** divisions per page (1:M at parse) |
| danceconvention.net | PDF | many URLs per event (one PDF per division) |

Read `scripts/extract.py` and `scripts/download.py` in full before starting —
most machinery you need already exists and must be **reused, not rewritten**.

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
- **Dance-style filtering**: a separate agent has added `NON_WCS_STYLE_RE` to
  both `download.py` and `extract.py` and is still refining it. Do **not** modify
  or remove that constant or its usages. Check for conflicts before editing either
  file.

---

## 3. What this rework changes and why

Three coupled changes. The taxonomy (§3b) is **already implemented** in
`extract.py`. Tasks remaining: §3a (event IDs in download.py + manifest) and
§3c (scoresheet ID scheme in extract.py).

### 3a. Event identity → a real `event_id` (reopen Phase 1) — DONE ✓

**Why:** event identity is currently reconstructed downstream from
`(site, event_name, dates)`. That's fragile — `event_name` slugs are lossy and
even encoding-inconsistent (the manifest holds both `Swing&Snow 2025` and
`Swing&amp;Snow 2025` for *one* event), which can split an event or collide two.
A stable event id fixes this and becomes the clean join key for the Phase-4
event-level lookups (region, tier, dance-style/WCS classification).

**Implemented:** each site's native event id is captured at discovery time and
namespaced as `{site_abbr}-{native_id}` → `sd-228`, `ee-swinglebell2025`,
`dc-301126`.

- `DiscoveredFinal` now has `event_id` and `source_event_id` fields.
- Each manifest record now has `event_id` and `source_event_id`.
- `download.py` writes `data/events.jsonl` (one row per event: `event_id`,
  `site`, `source_event_id`, `event_name`, `event_start`, `event_end`) at the
  end of every non-dry-run.
- **Migration:** the old manifest was deleted and `download.py` was re-run.
  Raw files in `data/raw/` are not re-downloaded (deterministic MD5 filenames);
  a fresh manifest with `event_id` in every record was written.

### 3b. Division taxonomy (covariate fields) — DONE ✓

Already implemented in `scripts/extract.py`. The finalised taxonomy:

- **`division_level`** — single flat field, `str | None`. Returns `None` when no
  level keyword is detected (e.g. unlevel Bachata J&J). Category wins over skill
  rung when both appear (`Masters Novice` → Masters). Combined rungs resolve to
  the higher rung (LEVEL_PATTERNS is ordered high-to-low, first match wins).
  Pro-Am is **not** a level — level is the amateur's skill rung.
- **`dance_format`** — `str | None`. Includes pro-am (with role) and switch as
  part of the format axis. Returns `None` when undetectable.
- `division_level` and `dance_format` are `null` in JSON when `None`.
- See `FORMAT_CODES`, `LEVEL_CODES`, and detection regexes in `extract.py` for
  the full implementation.

See also `briefs/division_inventory.txt` — the checkpoint inventory of all 382
distinct division blobs with their finalised classifications.

### 3c. Scoresheet ID scheme ★ TODO

- `id = "{event_slug}_{event_id}_{div_token}"`, e.g.
  `swingcouver_2025_sd-228_str_chp`.
  - `event_slug` = readable slug of `event_name` (decoration only).
  - `event_id` (e.g. `sd-228`) carries **global uniqueness**.
  - `div_token` — see below.
- **Delete** the existing `event_id_prefixes` / salting machinery in `extract.py`
  (it exists to handle slug collisions; `event_id` makes it unnecessary).
- **`div_token`**: `{format_code}_{level_code}` when both are in the standard
  maps; otherwise the raw division slug (with final/finals/финал stripped and
  J&J variants → `jnj`, Strictly/Strictly Swing → `str`).
- Residual intra-event collisions get a positional `_2` suffix (keep existing
  `make_id` collision logic, just update its inputs).
- Carry `event_id` and `source_event_id` into each parsed JSON.

---

## 4. ★ Finalised abbreviation map

The taxonomy checkpoint is at `briefs/division_inventory.txt`. The maps below
are **finalised** — do not change them without user sign-off.

### Format codes

| `dance_format` | code |
|---|---|
| Jack & Jill | `jnj` |
| Strictly | `str` |
| Classic | `classic` |
| Routine | `routine` |
| Rising Star | `risingstar` |
| Showcase | `showcase` |
| Switch Jack & Jill | `swjnj` |
| Switch Strictly | `swstr` |
| Pro-Am Jack & Jill (no role split) | `pamjnj` |
| Pro-Am Jack & Jill, amateur Leader | `pamljnj` |
| Pro-Am Jack & Jill, amateur Follower | `pamfjnj` |
| Pro-Am Strictly (no role) | `pamstr` |
| Pro-Am Strictly, Leader | `pamlstr` |
| Pro-Am Strictly, Follower | `pamfstr` |
| Anything else | raw fallback |

**Key format decisions:**
- Classic requires the literal word "classic" (or "team"). "Routines" alone ≠ Classic.
- Showcase and Routine are their own formats (not sub-types of Classic).
- Pro-Am Routine → raw fallback (not Pro-Am Classic).
- Switch/Switchly/Role Rotation are all Switch format. "Switchly" = Switch Strictly.
- All-American level: any blob containing the whole word `all` (that isn't already All-Star
  or All-Stars — those are checked first). "All Human" and similar are acceptable false positives.
  All-X blobs → Jack & Jill by convention (format inference mirrors this broadened pattern).
- Pro-am role detection: `(AmL)`/`(AmF)`, `L final`/`F final`, `LEADER`/`FOLLOWER`,
  `Am Lead`/`Am Follow` — role follows the amateur. "Pro Lead/Am Follow" → Follower.
- `\binter\b` matches Intermediate (French abbreviation convention).

### Level codes

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
| All-American (any blob with whole word "all", excl. All-Star) | `all` |
| Sophisticated | `sop` |
| Masters | `mas` |
| Junior | `jnr` |
| No level detectable | `null` → raw fallback |

---

## 5. Tasks (in order)

1. ~~**Inventory checkpoint** (§4)~~ — DONE. See `briefs/division_inventory.txt`.
2. ~~**download.py + manifest**~~ — DONE. `event_id`/`source_event_id` in
   `DiscoveredFinal` and every manifest record; `data/events.jsonl` written on
   each non-dry-run; manifest rebuilt from scratch via delete-and-rerun.
3. ~~**extract.py taxonomy**~~ — DONE. `division_level`, `dance_format`,
   `normalise_level`, `normalise_format`, `FORMAT_CODES`, `LEVEL_CODES` all
   finalised in `scripts/extract.py`.
4. **extract.py IDs**: new `id` scheme (`{event_slug}_{event_id}_{div_token}`),
   delete `event_id_prefixes` salting, keep positional intra-event suffix; carry
   `event_id`/`source_event_id` into each parsed JSON.
5. **Re-extract** (`--force`) and verify (§6).

---

## 6. Verification

- `extract.py` runs clean (no `IntegrityError` crash); skip summary only contains
  expected categories.
- Counts: similar to current ~418 parsed files (± new standard-set decisions and
  dance-style filtering); eepro 1:M expansion intact.
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
- Dump the final division→token mapping (`--dump-divisions`) and eyeball for
  collapses/leaks before declaring done.

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
- **Dance-style filtering**: `NON_WCS_STYLE_RE` is defined in both `download.py`
  and `extract.py` by a concurrent agent. Do not remove or modify it. The
  constant in `extract.py` is used to skip non-WCS divisions at extraction time.
- **IntegrityError in `--dump-divisions` mode**: a `try/except IntegrityError`
  wraps the validate call when `args.dump_divisions` is True, so the inventory
  run doesn't abort on edge-case sheets. This does NOT affect normal extraction
  (integrity errors still crash there). Keep this behaviour.
- **DC event_id**: the dc discovery function captures the native `eventId` from
  the `events` dict (available at discovery time) and sets it on `DiscoveredFinal`.
  The PDF URL alone does not contain the event id — it's only available during
  discovery, which is why this approach (capture at discovery, not derived from
  URL) was used.
