# Worked example: rank gaps (ℓ₁)

<!-- Source: site/src/lib/components/WorkedGaps.svelte
     Shown in the "How is this calculated?" dialog for these two metrics. Only the chosen metric's section appears.
     m = number of judges, n = number of competitors. -->

## Intro line (both metrics)

This metric counts rank gaps in plain places, so a gap of 4 places counts the same as four gaps of 1 place.

---

## Spearman footrule

### Spearman's footrule

The footrule adds up how many places apart two judges put each competitor, and divides by the largest total possible, which for $n = {n}$ competitors is $\lfloor n^2/2 \rfloor = \lfloor {n}^2/2 \rfloor = {max}$ (when one ranking is the reverse of the other). 0 means identical rankings, 1 means as different as possible. Lower is more agreement.

$$\text{footrule} = \frac{\sum_i |r_{a,i} - r_{b,i}|}{\lfloor n^2/2 \rfloor}$$

[Grid of the footrule for every pair of judges; clicking a pair shows a table of J_a rank, J_b rank and |diff| for each competitor, with a Total row, then $\text{footrule} = \frac{total}{max} = value$.]
<!-- Grid's accessible label: "Normalised footrule for each pair of judges" -->

The metric is the mean of the footrule over all {pairs} pairs of judges:

✓ check line: "Mean footrule = {value}"

---

## Mean absolute deviation (from the median)

### Mean absolute deviation of each competitor's ranks

This looks at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with ranks $r_1, \dots, r_m$ and median $\tilde r$, take the average distance from the median:

$$\text{mean absolute deviation} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \tilde r|$$

The median is the natural centre for absolute distances: no other point gives a smaller total. The metric starts from the average over the {n} competitors. That's in places, so lower means more agreement.

[Rank table. Extra columns: **Median** · **Mean abs. dev.** (tooltip: "Mean absolute deviation from the median"; footer is the average)]

The bottom row of the last column is its average over competitors, in places. *(small, grey)*

**Normalising.** Because the average is in places, it can't be compared across finals of different sizes. So the metric normalises it, dividing by $n/4$, which is what the average would be if half the panel ranked in order and half in exact reverse. No panel can go above it. Then 0 means every judge agreed on every competitor, and 1 means the panel was split as far as it could be. A panel with an odd number of finalists or judges can't quite reach it, so the most split such a panel can look is a little under 1.

$$\frac{mad}{n/4} = \dots = {value}$$ *(numbers substituted)*

✓ check line: "Mean absolute deviation, normalised = {value}"

Normalising this way is a first pass. It removes the main effect of field size, but not all of it: random rankings don't land at the same value for every field and panel size, so a chance-based correction is planned. *(small, grey)*
