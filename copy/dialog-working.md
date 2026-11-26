# "How is this calculated?" dialog

<!-- Source: site/src/lib/components/ExplorePage.svelte (the `working` Modal), Standing.svelte, percentiles.js.
     This is the frame; the body below it is the worked text for the chosen metric
     (worked-squared.md, worked-gaps.md, worked-head-to-head.md, worked-top-n.md). -->

**Small heading above the title:** How is this calculated?
**Title:** a dropdown of metrics, showing each metric's full name (see metric-descriptions.md)

**Scoresheet line:** **{competition name}** ({date})

**Small text:**
{A scoresheet chosen at random. | The scoresheet you chose. | The scoresheet you clicked. | *(nothing, if it came from a link)*} To see another, close this and choose an event or click a point in the box plot, or [pick one at random]{(shows "loading…" while loading)}. You can also [see details and other metrics for this scoresheet].

## Value and percentile box

| Label | Content |
|---|---|
| VALUE | {value}, and underneath: "Higher means more agreement" / "Lower means more agreement" |
| PERCENTILE | {Nth} with a marker track, and underneath the explanation below |

**Percentile explanation:**
More agreement than {X%} of all {N} {Jack & Jill | Strictly} finals{ with at least 6 competitors}, on this metric.
<!-- {X%} is shown as "over 99%" at the top end and "under 1%" at the bottom. "with at least 6 competitors" appears only for the top-3 metrics. -->

**When the final has too few competitors for this metric** (the percentile is "–"):
Not ranked: finals with fewer than 6 competitors are left out of this metric's charts.
