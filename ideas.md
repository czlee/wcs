# Ideas

A scratchpad for ideas that aren't planned yet. Once an idea is committed to, it moves into `plan.md`.

## Explorer (`site/`, `ExplorePage.svelte`)

For now the y-axis is always a divergence metric. These ideas are about how the x-axis is grouped and which scoresheets get included.

### Filters

- **Field size.** This would show at a glance whether field size explains most of the variance *within* a level. It matters because field size changes the metrics directly: a ranking of 5 has far less room to disagree than a ranking of 15, and top-N chance agreement depends on n. We already have this as `num_competitors`. It ranges from 5 to 40, with peaks at 10, 12 and 15, and almost nothing above 16. Bins of 5–7 / 8–10 / 11–13 / 14+ give groups of 652 / 1,009 / 528 / 362 sheets.
- **Panel size.** We already have this as `num_judges`. Panels are almost all 5, 7 or 9 judges (out of ~2,550 sheets, only ~40 have some other size), so a filter of 5 / 7 / 9 / other would work.
- **Date.** We already have this as `event_date`. It could be a date range or a year picker. Coverage at present is events that start in 2024–2025.
- **Region.** We don't have this yet. It needs Phase 4A (`lookups/regions.json`, keyed on `event_id`/`event_name`; see `plan.md`). We'd want coarse buckets (e.g. North America / Europe / Oceania / …) so that each group has a usable n.
- Another dimension we already have: source site (`site`), which is mostly useful as a check for parser artefacts.
- Later: competition format (spotlights / clusters / all-skate), if Phase 4B ever happens.

### Changing the x-axis

- Eventually the x-axis could switch from division level to one of the dimensions above (panel size, field size, region, year), with level becoming a filter or a colour.
- The same chart code should cover this as long as each dimension is categorical or binned.
- Keep in mind: once we're filtering *and* regrouping, some cells will be tiny, so the charts need to show n and grey out or hide cells below a minimum (the way `minN` already does for top-N).

## Data collection

- ~~**Grab the 2026 competitions.**~~ Done 2026-11-22: downloaded 2026-01-01 to 2026-11-22 (`download.py --start 2026-01-01 --end 2026-11-22`), then extract → metrics → `export_site_data.py`. `events.jsonl` now covers 2024 to Nov 2026. Re-run the same steps with a later `--end` to top up.
