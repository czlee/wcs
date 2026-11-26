# Worked example: top-N agreement (overlap and Jaccard @ 3)

<!-- Source: site/src/lib/components/WorkedTop.svelte
     Shown in the "How is this calculated?" dialog for the four top-3 metrics. The text covers overlap and Jaccard, with
     and without the chance correction; whichever isn't the chosen metric is dimmed "for comparison". N = 3.
     m = number of judges, n = number of competitors. -->

## Opening

This metric ignores the order within the top 3 places and asks only *who* made them. For a pair of judges, take the sets $A$ and $B$ of competitors each ranked 1st to 3rd, and count how many are in both. There are two ways to turn that into a score: the overlap divides it by 3, and the Jaccard index divides it by how many are in either set.

## Which one you're looking at *(small, grey)*

The metric you're looking at is the {overlap | Jaccard index}{, corrected for chance (the last step) | , without a correction for chance}. The [[...|Jaccard index]] | [[...|overlap]] {is | and the chance correction are} dimmed, for comparison.

$$\text{overlap} = \frac{|A \cap B|}{3} \qquad\qquad \text{Jaccard} = \frac{|A \cap B|}{|A \cup B|}$$

Both sets have 3 members, so with $k$ in common, $\text{Jaccard} = \frac{k}{6 - k}$: for a single pair it carries the same information as overlap on a different scale. Averaged over pairs, the two differ slightly.

[Grid of the number of competitors in both judges' top 3, for every pair of judges. Accessible label: "Number of competitors in both judges' top 3".]

### When a pair of judges is selected

Heading: J{a} {name} and J{b} {name}
Two lists, headed "J{a}'s top 3" and "J{b}'s top 3", with the competitors in both highlighted.
Highlighted: in both ({k}). In either: {u}. *(small)*

$$\text{overlap} = \frac{k}{3} = value \qquad\qquad \text{Jaccard} = \frac{k}{u} = value$$

Cells show how many competitors are in both judges' top 3, out of 3. *(small, grey)*

Averaging over all {pairs} pairs of judges:

✓ check lines: "Mean overlap @ 3 = {value}" · "Mean Jaccard @ 3 = {value}"

## Correcting for chance

*(This section is dimmed when the chosen metric isn't a chance-corrected one.)*

Two judges picking their top 3 at random would still share some competitors, and more often in a small final. If each judge's top 3 were a random 3 of the $n = {n}$ competitors, the number in both, $i$, would follow a hypergeometric distribution, with expected values

$$\mathbb{E}[\text{overlap}] = \frac{3}{n} = value$$

$$\mathbb{E}[\text{Jaccard}] = \sum_i \frac{\binom{3}{i}\binom{n-3}{3-i}}{\binom{n}{3}} \cdot \frac{i}{6 - i} = {terms} = value$$

The corrected value rescales the mean over judge pairs, $x$, so that 0 is chance-level agreement and 1 is identical top 3s:

$$\text{corrected} = \frac{x - \mathbb{E}[x]}{1 - \mathbb{E}[x]}$$

$$\text{overlap} = \frac{x - E}{1 - E} = value \qquad\qquad \text{Jaccard} = \frac{x - E}{1 - E} = value$$

✓ check lines: "Mean overlap @ 3, chance-corrected = {value}" · "Mean Jaccard @ 3, chance-corrected = {value}"

This is a naive, first-pass correction. Real judges' top 3s aren't random: they're drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects the result. *(small, grey)*

## Callout: shown only when the final has fewer than 6 competitors

With only {n} competitors, any two top-3 sets must share at least $2 \times 3 - {n} = {k}$ {competitor | competitors}, so this metric can't reach its full range. Finals of fewer than 6 are left out of the charts for this metric.
