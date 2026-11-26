# Worked example: head-to-head order (Kendall τ)

<!-- Source: site/src/lib/components/WorkedHeadToHead.svelte
     Shown in the "How is this calculated?" dialog for both Kendall metrics. The text is shared; the metric being
     viewed is switched with `isTau`. The other metric's formulas are dimmed "for comparison".
     m = number of judges, n = number of competitors. -->

## Opening paragraph

**If the chosen metric is the τ distance:**
The **Kendall $\tau$ distance** counts how many pairs of competitors in two judges' rankings are different. Here we normalise it to a share of all pairs of competitors, from 0 to 1. The **mean pairwise normalised** Kendall $\tau$ distance averages this over every pair of judges on the panel.

**If the chosen metric is the correlation:**
The **Kendall rank correlation coefficient**, often known as **Kendall's $\tau$**, counts how many pairs of competitors in two judges' rankings are the same and different. The **mean pairwise** Kendall rank correlation coefficient averages this over every pair of judges on the panel.

## Which one you're looking at *(small, grey)*

The metric you're looking at is the {mean pairwise Kendall correlation | mean pairwise normalised Kendall τ distance}. The [[tau_distance|mean pairwise normalised Kendall τ distance]] | [[mean_pairwise_tau|mean pairwise Kendall correlation]] is dimmed, for comparison.

## Notation *(small, grey)*

Since both metrics are based on Kendall's $\tau$, the notation can get confusing. We'll use $\tau$ for the correlation coefficient, and $d_\tau$ for the distance. Each is worked out for a pair of judges $J_i$ and $J_j$, so we write $\tau(J_i, J_j)$ and $d_\tau(J_i, J_j)$. A bar, as in $\bar\tau$ and $\bar d_\tau$, means the mean over every pair of judges.

## Concordant and discordant pairs

Take two judges and any two competitors. If both judges put the same competitor ahead, that competitor pair is **concordant**; if they disagree on who goes ahead, it's **discordant**. With $n = {n}$ competitors there are $\tfrac{n(n-1)}{2} = {pairs}$ competitor pairs. For each pair of judges:

$$d_\tau(J_i, J_j) = \frac{\text{discordant}}{{pairs}} \qquad\qquad \tau(J_i, J_j) = \frac{\text{concordant} - \text{discordant}}{{pairs}}$$

[Grid for every pair of judges (click to select). Accessible label: "Kendall's τ for each pair of judges" or "Share of competitor pairs ordered differently, for each pair of judges".]

### When a pair of judges is selected

Heading: J{a} {name} and J{b} {name}

Competitors in J{a}'s order, with both judges' ranks for each along the top and down the left. Each cell is one competitor pair: ✓ concordant, ✗ discordant. Hover over or tap a cell to see how a pair is concordant or discordant.

**Verdict line for the highlighted cell:**
- Agree: J{a} and J{b} both put **{X}** ahead of **{Y}**, so this competitor pair is concordant ✓
- Disagree: J{a} put **{X}** ahead, but J{b} put **{Y}** ahead, so this competitor pair is discordant ✗

(Table labels: "J{a}'s rank", "J{b}'s rank", "Competitor". Tooltip on column initials and competitor names: the competitor's full name.)

$$d_\tau(J_a, J_b) = \frac{D}{pairs} = value \qquad\qquad \tau(J_a, J_b) = \frac{C - D}{pairs} = value$$ *(numbers substituted)*

## The metric itself

**τ distance:** The **mean pairwise normalised Kendall $\tau$ distance**, written $\bar d_\tau$, is the mean of $d_\tau$ over all {pairs} pairs of judges. It reads as "on average, two judges order {x}% of head-to-heads differently".

$$\bar d_\tau = \frac{1}{{pairs}} \sum_{i<j} d_\tau(J_i, J_j)$$  ✓ check line

**Correlation:** The **mean pairwise Kendall correlation**, written $\bar\tau$, is the mean of $\tau$ over all {pairs} pairs of judges.

$$\bar\tau = \frac{1}{{pairs}} \sum_{i<j} \tau(J_i, J_j)$$  ✓ check line

## Aside (small type)

**A curiosity:** Every pair of competitors is either concordant or discordant, so $\text{concordant} = {pairs} - \text{discordant}$ and the two metrics are linked:

$$\bar d_\tau = \frac{1 - \bar\tau}{2} \qquad \left(\text{here: } {x} = \frac{1 - {τ̄}}{2}\right)$$

So each is a reversed and scaled version of the other:

[Diagram: two scale bars. Labels above: "perfect disagreement" / "random judging" / "perfect agreement". Bar for $\bar d_\tau$: 1 · 0.5 · 0. Bar for $\bar\tau$: −1 · 0 · 1.]
