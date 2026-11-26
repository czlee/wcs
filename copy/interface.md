# Interface copy

<!-- Everything else a reader sees. Source file in each section heading. -->

## Page titles (browser tab and search results)

<!-- site/src/routes/+page.svelte and strictly/+page.svelte -->

| Page | Title | Description |
|---|---|---|
| Jack & Jill | How much do WCS judges disagree? Jack & Jill finals | How different judges' rankings are in West Coast Swing Jack & Jill finals, one metric at a time. |
| Strictly | How much do WCS judges disagree? Strictly finals | How different judges' rankings are in West Coast Swing Strictly finals, one metric at a time. |

## Draft banner and footer

<!-- site/src/routes/+layout.svelte; the banner shows only while the site is a draft -->

**Banner:** **DRAFT** · Work in progress: numbers, wording and layout may change.

**Footer:** Built by Chuan-Zheng Lee using Claude Code. Exploratory, not adjusted for panel or field size; see the [limitations]. This site doesn't rate individual judges.

## Top bar

<!-- ExplorePage.svelte -->

- Brand: WCS judge agreement *(with a DRAFT tag while a draft)*
- Format switch: Jack & Jill | Strictly
- Count: {N} finals, {first date} to {last date} *(when filtered: "{k} of {N} finals, …")*
- Warning button: ⚠ Exploratory: read the limitations
- About

## Metric rail

- Select label (narrow screens): Metric
- Rail heading: Metrics
- Family headings and metric menu names: see `metric-descriptions.md`

## Main heading area

- Heading: the metric's full name (see `metric-descriptions.md`)
- Button: How is this calculated?
- Direction line: ● Higher means more agreement  | ● Lower means more agreement {· finals of 6 or more competitors *(top-3 metrics only)*}

## Panels under the charts

- Panel headings: **What it measures** · **Caveats for this metric**
- Link after the first panel's text: Learn more
- Under the caveats: Also see the [limitations]. *(or "See the limitations." when the metric has no caveats of its own)*

## Filters

<!-- FilterBar.svelte, dimensions.js -->

- Filter labels: Judges · Year · Region · Finalists
- **Finalists tooltip:** The number of couples in the final. Some metrics depend on field size, so narrowing this range can help take that variable out of the comparison.
- Slider handle labels (for screen readers): "Fewest finalists", "Most finalists"; the top stop reads "16+"
- Button tooltip: Ctrl-click or Shift-click to choose several *(or, once one is chosen:)* Ctrl-click or Shift-click to add or remove from the choice
- Hint (when a button filter is on): Ctrl/Shift-click to choose several
- Button: Clear filters

### Regions

<!-- Region names and which countries are in each: site/src/lib/regions.js (not copy, but the names show in the Region filter) -->

## Charts

<!-- MetricChart.svelte, stats.js -->

- Side labels on each chart: "more agreement" / "less agreement" (which end is which depends on the metric)
- Marker at zero on chance-corrected metrics: "chance"
- Bar chart caption: Mean ± 1.96 × standard error ([provisional]{tip: Scoresheets aren't independent: the same judges sit on many panels. The error bars are the 95% confidence interval assuming independence, so they're probably too narrow.}), by level
- Box plot caption: Every scoresheet, with quartiles
- Level short labels under the charts: New · Nov · Int · Adv · AlS · Chp, and "n=…" beneath
- Level full names (tooltips and elsewhere): Newcomer · Novice · Intermediate · Advanced · All-Star · Champions
- Empty state: No finals match these filters
- Hover on a bar: "{Level}: mean {value}", and, for groups with fewer than 10 scoresheets, "Fewer than 10 scoresheets" *(these groups are drawn grey, without an interval)*
- Hover on a box: "{Level}, {k} scoresheets" / "median {v}" / "quartiles {a} to {b}" / "whiskers {a} to {b}"
- Hover on a point: the scoresheet's name and its value *(see MetricChart.svelte `pointLines` if you want to change the format)*
- Accessible chart labels: "{metric} (higher/lower means more agreement): mean by level" / "…: distribution by level"

## Highlighted scoresheet box

<!-- SheetPicker.svelte -->

- Label: Highlighted scoresheet
- Placeholder: Choose an event…
- Before enough is typed: Type at least 3 characters to find a scoresheet
- No results: No matching scoresheets
- Too many: {50} of {N} scoresheets: type to narrow the list
- Otherwise: {N} scoresheet(s)
- Under the box: {date · location · other details} · {m judges × n competitors}
- When the scoresheet isn't ringed in the box plot: [Not in the current view]{tip: No point in the box plot is ringed, because this scoresheet {has too few finalists for this metric | is outside the filters}.}
- Link: details and all metrics for this scoresheet

## Percentile wording

<!-- percentiles.js; shown in the working dialog and as tooltips in the profile table -->

- More agreement than {X%} of all {N} {Jack & Jill | Strictly} finals{ with at least 6 competitors}, on this metric.
- Not ranked: finals with fewer than 6 competitors are left out of this metric's charts.

## Recalculation check (✓)

<!-- Check.svelte, MetricsTable.svelte -->

- Tooltip on ✓: Recalculated in your browser; matches the precomputed value used in the charts ({value})
- If it doesn't match: ✗ doesn't match the precomputed value used in the charts ({value})
