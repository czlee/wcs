# About dialog

<!-- Source: site/src/lib/components/ExplorePage.svelte (the `about` Modal).
     Opens by itself on a first visit (then leads on to the limitations); also from "About" in the top bar.
     {…} are filled in. The links are to scoring.dance, eepro.com, danceconvention.net, claude.ai and github.com/czlee/wcs. -->

**Small heading above the title:** About
**Title:** How much do WCS judges disagree?

By Chuan-Zheng Lee, with implementation by Claude *(byline; the second part is styled as a credit)*

In a West Coast Swing final, every judge ranks every competitor, and relative placement combines those rankings into the result. This looks at the rankings before they're combined: how different are the judges' rankings from each other, and does that vary by division level? It covers **{N} {Jack & Jill | Strictly} finals** from {first date} to {last date}. {Strictly | Jack & Jill} finals are a click away in the top bar.

There are many ways to measure how far apart rankings are, and they don't all answer the same question. This uses eleven, in four families. Pick one on the left (or step through them with ← and →); the bar chart shows its mean by level, and the box plot shows every final. Field and panel sizes differ between levels, so you can narrow the charts to finals with similar numbers of finalists or judges; the vertical axes stay put, so you can compare. The address in your browser always links to what you're looking at.

Every number can be checked. "How is this calculated?" recalculates the metric in your browser, step by step, and checks the result against the analysis. Choose a scoresheet to highlight at the top right, to ring it in the box plot and work through it; its "details" show the judges' rankings, every metric and a link to the published scoresheet. Or click a point in the box plot for its working.

The method and design decisions are mine; the code, including the data processing and this website, was largely written by [Claude](https://claude.ai/), under my direction.

Data: published finals scoresheets from [scoring.dance](https://scoring.dance/), [eepro.com](https://eepro.com/) and [danceconvention.net](https://danceconvention.net/), exported {date} from commit `{commit}`. Code: [czlee/wcs](https://github.com/czlee/wcs).

**Callout:** **This is exploratory.** Panel and field sizes differ between levels, and most of these metrics depend on them. [Read the limitations] before reading anything into a difference.

**Button:** Continue
