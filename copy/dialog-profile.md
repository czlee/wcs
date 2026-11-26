# Scoresheet profile dialog

<!-- Source: ExplorePage.svelte (the `profile` Modal), SheetMeta.svelte, MetricsTable.svelte, percentiles.js.
     Opened with "details and all metrics for this scoresheet" under the highlighted-scoresheet box, or from the working dialog. -->

**Small heading above the title:** Scoresheet profile
**Title:** the scoresheet's name, which is also a search box for choosing another (placeholder "Choose an event…")

## Facts list

Labels: Event · Competition · Date · Location *(only if known)* · Counted as *({Jack & Jill | Strictly}, {level})* · Size *({m} judges × {n} competitors)* · Source *(link)*

**Link under the facts (with the Who Woulda Won icon):** See who wins under different voting systems on **Who Woulda Won**

## Rank table

**Caption:** Each judge's ranks (1 = first), competitors in the order on the scoresheet

## Every metric

**Heading:** Every metric for this scoresheet

Choose a metric to see its working. A ✓ means that recalculating it in your browser gives the value used in the charts. The percentile compares this final with all {Jack & Jill | Strictly} finals, at every level and whatever the filters: 100th is the most agreement, whichever way the metric runs. It isn't adjusted for field or panel size, so for example a small final tends to rank high on the metrics measured in places.

**Table columns:** Metric · *(direction)* · Value · *(check)* · Percentile · *(marker)*
**Direction note, per row:** higher = more agreement / lower = more agreement
**✓ tooltip:** Recalculated in your browser; matches the precomputed value used in the charts ({value})
**If it doesn't match:** ✗ precomputed: {value}
**Percentile tooltip:** the same explanation as in the working dialog (see `dialog-working.md`), or "Not ranked: …" with a "–"
