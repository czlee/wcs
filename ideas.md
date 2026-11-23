# Ideas

A scratchpad for ideas that aren't planned yet. Once an idea is committed to, it moves into `plan.md`.

## Explorer (`site/`, `ExplorePage.svelte`)

For now the y-axis is always an agreement metric. These ideas are about how the x-axis is grouped and which scoresheets get included.

### Filters

Field size, panel size, region and year (a picker for 2024–2026) are done: see "Results site: filters" in `plan.md`. Still ideas (each would be another entry in `site/src/lib/dimensions.js`):

- Another dimension we already have: source site (`site`), which is mostly useful as a check for parser artefacts.
- Later: competition format (spotlights / clusters / all-skate), if Phase 4B ever happens.

### Changing the x-axis

- Eventually the x-axis could switch from division level to one of the dimensions above (panel size, field size, region, year), with level becoming a filter or a colour.
- The same chart code should cover this as long as each dimension is categorical or binned.
- Keep in mind: once we're filtering *and* regrouping, some cells will be tiny, so the charts need to show n and grey out or hide cells below a minimum (the way `minN` already does for top-N).

### Colouring points by a dimension

- Colour the points (or boxes) by a second dimension, e.g. field-size bin, panel size, year or region. This is the Tableau/Hex-style "colour" shelf. It would let us see within-level structure without filtering anything away, e.g. whether the low-agreement sheets in a level are mostly the small fields.
- It should use the same dimension list as filters and the x-axis, so one definition of each dimension (label, accessor, bins) serves all three roles: filter, group-by and colour-by.
- Needs a categorical palette that stays legible in both themes, and a legend that shows n per colour.

## Data collection

- ~~**Grab the 2026 competitions.**~~ Done 2026-11-22: downloaded 2026-01-01 to 2026-11-22 (`download.py --start 2026-01-01 --end 2026-11-22`), then extract → metrics → `export_site_data.py`. `events.jsonl` now covers 2024 to Nov 2026. Re-run the same steps with a later `--end` to top up.
