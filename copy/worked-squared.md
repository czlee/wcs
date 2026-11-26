# Worked example: rank gaps squared (ℓ₂)

<!-- Source: site/src/lib/components/WorkedSquared.svelte
     Shown in the "How is this calculated?" dialog, for the metric chosen. Only the section for the chosen metric
     appears, so each must stand alone (don't refer to metrics the reader can't see, except via [[links]]).
     m = number of judges, n = number of competitors on the scoresheet. Interactive tables (the rank table, the judge-pair grid) sit
     where marked in [brackets]; their labels are listed at the end of each section. -->

## Intro line (all three metrics)

This metric is built from **squared** rank gaps, so one big disagreement counts for more than several small ones adding up to the same number of places.

---

## Kendall's W

### Kendall's W, step by step

This final has $m = {m}$ judges and $n = {n}$ competitors. Add up the ranks each competitor got from the {m} judges. If the judges agreed completely, these rank sums would be as far apart as they can get: one competitor would get {m} firsts (a sum of {m}), the next {m} seconds (a sum of {2m}), and so on. If the judges' rankings had nothing in common, every competitor's sum would tend towards the same middle value, $\tfrac{m(n+1)}{2} = \tfrac{{m} \times {n+1}}{2} = {rBar}$.

[Rank table. Extra columns: **Rank sum** · **− {rBar}** (tooltip: "Rank sum minus m(n+1)/2") · **Squared** (footer: S = {S})]

[S]{tip: The sum of the squared deviations of the rank sums from m(n+1)/2, shown at the bottom of the last column.} measures how spread out the rank sums are. $W$ divides $S$ by the largest value it could take, $\tfrac{1}{12} m^2(n^3 - n)$:

$$W = \frac{S}{\tfrac{1}{12}\, m^2(n^3 - n)}$$ *(numbers substituted for this scoresheet)*

✓ check line: "W = {value}" with tooltip "Recalculated in your browser; matches the precomputed value used in the charts ({value})"

$W$ runs from 0 (no common ordering at all) to 1 (every judge gave the same ranking). One catch: if the judges ranked at random, $W$ would still average $\tfrac{1}{m}$, here $\tfrac{1}{{m}} = {1/m}$. So a bigger panel gets a lower $W$ from chance alone, and $W$ isn't directly comparable across panel sizes.

**Aside (small type): How this relates to Spearman's ρ:** the [[mean_pairwise_rho|mean pairwise Spearman $\rho$]], $\bar\rho$, is another of the metrics on this site, which averages the agreement between each pair of judges. For rankings without ties the two are exactly related: $\bar\rho = \frac{mW - 1}{m - 1}$, so for any one scoresheet they carry the same information. Here $W = {W}$, giving

$$\bar\rho = \frac{mW - 1}{m - 1}$$ *(numbers substituted)*

The difference is the scale: $\bar\rho$ is 0 for random judging whatever the panel size, whereas $W$ is $\tfrac{1}{m}$, which is why $\bar\rho$ is the one to compare across panel sizes.

---

## Mean pairwise Spearman ρ

### Mean pairwise Spearman ρ

[Spearman's $\rho$]{tip: Spearman's rank correlation: 1 if two rankings are identical, −1 if one is the reverse of the other, about 0 if unrelated.} compares two judges' rankings. For each competitor, take the difference $d$ between the two ranks, and add up the squares, $\sum d^2$. That's 0 if the rankings are identical, and with $n = {n}$ competitors it's at most $\tfrac{1}{3}\,n(n^2 - 1) = {max}$, when one ranking is the reverse of the other. ρ divides $\sum d^2$ by that maximum and rescales it to run from 1 (identical) to −1 (reversed):

$$\rho = 1 - 2 \times \frac{\sum d^2}{\tfrac{1}{3}\, n(n^2 - 1)}$$

Here it is for every pair of judges:

[Grid of ρ for every pair of judges; clicking a pair shows a table of J_a rank, J_b rank, d, d² for each competitor, then the formula with numbers.]
<!-- Grid's accessible label: "Spearman's ρ for each pair of judges" -->

The metric, $\bar\rho$, is the mean of these values over all {pairs} pairs of judges:

$$\bar\rho = \frac{1}{{pairs}} \sum_{\text{pairs}} \rho = \frac{{sum}}{{pairs}} = {mean}$$

✓ check line: "ρ̄ = {value}"

If the judges ranked at random, $\bar\rho$ would average 0, whatever the panel size, so panels of different sizes are compared fairly in that respect.

**Aside (small type): How this relates to Kendall's W:** [Kendall's $W$]→[[kendall_w]] is another of the metrics on this site, which measures how much the whole panel agrees on one order. For $m = {m}$ judges and rankings without ties, the two are exactly related: $\bar\rho = \frac{mW - 1}{m - 1}$, so for any one scoresheet they carry the same information. Here $W = {W}$, giving

$$\frac{mW - 1}{m - 1} = \dots = {value}$$

the same as the mean above. The difference is the scale: a random panel averages $\bar\rho = 0$ whatever its size, but $W$ averages $\tfrac{1}{m}$.

---

## Standard deviation of ranks

### Standard deviation of ranks

This looks at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with ranks $r_1, \dots, r_m$ and mean $\bar r$, the standard deviation is

$$\text{standard deviation} = \sqrt{\frac{1}{m}\sum_{j=1}^{m} (r_j - \bar r)^2}$$

(dividing by $m$, not $m - 1$). The metric starts from the average over the $n = {n}$ competitors. That's in places, so lower means more agreement.

[Rank table. Extra columns: **Mean** · **Standard deviation** (tooltip: "Population standard deviation (÷ m)"; footer is the average)]

The bottom row of the last column is its average over competitors, in places. *(small, grey)*

**Normalising.** Because the average is in places, it can't be compared across finals of different sizes. So the metric normalises it, dividing by $\sqrt{(n^2-1)/12}$, the largest the average can be. That is also the standard deviation of the ranks a single judge would give a random competitor, so 1 means the judges disagreed as much as judges can without agreeing at all, and 0 means every judge agreed on every competitor.

$$\frac{sd}{\sqrt{(n^2-1)/12}} = \dots = {value}$$ *(numbers substituted)*

✓ check line: "Standard deviation of ranks, normalised = {value}"

This is a first pass. It removes the main effect of field size, but not all of it: random rankings don't land at the same value for every panel size (a bit under 1, and further under for small panels), and a panel of two judges can't reach 1. A chance-based correction is planned. *(small, grey)*

**Aside (small type): How this relates to Kendall's W:** [Kendall's $W$]→[[kendall_w]] is another of the metrics on this site, which measures how much the whole panel agrees on one order; here $W = {W}$. The squared standard deviations (the variances) carry the same information as $W$ for a given field size. For rankings without ties, their average over competitors is exactly $\tfrac{n^2 - 1}{12}(1 - W)$:

$$\tfrac{n^2 - 1}{12} \times (1 - W) = {x}, \quad \text{and the mean variance here is } {y}.$$ *(numbers substituted)*

The metric averages the standard deviations rather than the variances, so it isn't exactly a rescaling of $W$, but it's close.
