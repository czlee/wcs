# Metric descriptions

<!-- Source: site/src/lib/about.js (ABOUT), site/src/lib/families.js (names, families).
     Shown in the two panels under the charts: "What is {title, in lower case unless it begins with Kendall or Spearman}? (Learn more)" (a heading with the Learn more link, then one
     sentence, then a red-to-green scale) and "Caveats for this metric" (the bullets). If a metric has no caveats, the panel
     shows only "See the limitations." Plain text, [[key|text]] links only. -->

<!-- Scales: centred in the panel; values always in numeric order, lowest on the left, coloured red to green (green to red when
     lower is better). A middle point (random ranking) sits roughly where its value falls along the scale, not always at the centre. -->

<!-- Under the caveats list the panel always says: "Also see the limitations." (or "See the limitations." if there are no caveats). -->

## Families

<!-- Group headings in the metric menu/rail. -->

1. Rank gaps squared (ℓ₂)
2. Rank gaps (ℓ₁)
3. Head-to-head order
4. Top-N agreement

## 1. Kendall's W

<!-- key: kendall_w · family: Rank gaps squared (ℓ₂) · menu name: "Kendall's W" -->

**Title:** Kendall's W
**Higher means more agreement.**

**Sentence** (under the heading "What is Kendall's W? (Learn more)"):
How spread out the competitors’ rank sums are, compared with the most they could be.

**Scale:**
- Left: 0 — max disagreement
- Middle: 1/m — random ranks (sits left of centre)
- Right: 1 — fully unanimous

**Caveats:**
- If the judges ranked at random, W would still average 1/m for a panel of m judges, so a bigger panel gets a lower W from chance alone. W isn’t directly comparable across panel sizes; the [[mean_pairwise_rho|mean pairwise Spearman ρ]] is the fairer of the two for that.

## 2. Spearman ρ

<!-- key: mean_pairwise_rho · family: Rank gaps squared (ℓ₂) · menu name: "Spearman ρ" -->

**Title:** Mean pairwise Spearman ρ
**Higher means more agreement.**

**Sentence** (under the heading "What is mean pairwise Spearman ρ? (Learn more)"):
How closely pairs of judges’ rankings track each other, from the squared gaps between their ranks, averaged over every pair.

**Scale:**
- Left: −1/(m−1) — max disagreement
- Middle: 0 — random ranks (sits near the left)
- Right: 1 — fully unanimous

**Caveats:**
- For any one scoresheet it carries the same information as [[kendall_w|Kendall’s W]] (with m judges, ρ̄ = (mW − 1)/(m − 1)), rescaled so that chance is 0 for every panel size.

## 3. Standard deviation

<!-- key: sd_rank_norm · family: Rank gaps squared (ℓ₂) · menu name: "Standard deviation" -->

**Title:** Mean normalised standard deviation of ranks
**Lower means more agreement.**

**Sentence** (under the heading "What is mean normalised standard deviation of ranks? (Learn more)"):
How much the judges’ ranks for each competitor vary, averaged over competitors and scaled by the field size.

**Scale:**
- Left: 0 — fully unanimous
- Middle: *(no middle point)*
- Right: 1 — max disagreement

**Caveats:**
- Normalised for field size only roughly. That removes the main effect of field size, but random rankings don’t land at the same value for every panel size (a bit under 1, and further under for small panels), and a panel of two judges can’t reach 1. A proper chance correction is planned.

## 4. Spearman footrule

<!-- key: footrule_mean · family: Rank gaps (ℓ₁) · menu name: "Spearman footrule" -->

**Title:** Mean Spearman footrule
**Lower means more agreement.**

**Sentence** (under the heading "What is mean Spearman footrule? (Learn more)"):
How many places apart two judges put each competitor, added up, as a share of the most possible, averaged over every pair.

**Scale:**
- Left: 0 — fully unanimous
- Middle: ≈0.66 — random ranks (sits right of centre)
- Right: 1 — max disagreement

**Caveats:**
*(none; the panel just says "See the limitations.")*

## 5. Absolute deviation

<!-- key: mean_abs_rank_dev_median_norm · family: Rank gaps (ℓ₁) · menu name: "Absolute deviation" -->

**Title:** Mean normalised absolute deviation from median
**Lower means more agreement.**

**Sentence** (under the heading "What is mean normalised absolute deviation from median? (Learn more)"):
How far each judge’s rank for a competitor is from the median, averaged over judges and competitors and scaled by the field size.

**Scale:**
- Left: 0 — fully unanimous
- Middle: *(no middle point)*
- Right: 1 — panel split in two

**Caveats:**
- Normalised for field size only roughly, by dividing by n/4, the most the average can be: it’s what the average is when half the panel ranks in order and half in exact reverse. Some panels (an odd number of finalists or of judges) can’t quite reach it, so a maximally split panel reads a little under 1 there. That removes the main effect of field size, but random rankings don’t land at the same value for every field and panel size, so some of it remains. A proper chance correction is planned.

## 6. Kendall τ distance

<!-- key: tau_distance · family: Head-to-head order · menu name: "Kendall τ distance" -->

**Title:** Mean pairwise normalised Kendall τ distance
**Lower means more agreement.**

**Sentence** (under the heading "What is mean pairwise normalised Kendall τ distance? (Learn more)"):
The share of head-to-heads (pairs of competitors) that two judges put in opposite orders, averaged over every pair of judges.

**Scale:**
- Left: 0 — fully unanimous
- Middle: 0.5 — random ranks (sits right of centre, clear of the right-hand value)
- Right: (m+1)/(2m) — max disagreement

**Caveats:**
- Random judging averages 0.5 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.

## 7. Kendall correlation

<!-- key: mean_pairwise_tau · family: Head-to-head order · menu name: "Kendall correlation" -->

**Title:** Mean pairwise Kendall rank correlation coefficient
**Higher means more agreement.**

**Sentence** (under the heading "What is mean pairwise Kendall rank correlation coefficient? (Learn more)"):
Agreeing minus disagreeing head-to-heads between two judges, as a share of all of them, averaged over every pair of judges.

**Scale:**
- Left: −1/m — max disagreement
- Middle: 0 — random ranks (sits near the left)
- Right: 1 — fully unanimous

**Caveats:**
- Random judging averages 0 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.

## 8. Overlap @ 3 (cc)

<!-- key: overlap_at_3_cc · family: Top-N agreement · menu name: "Overlap @ 3 (cc)" · charted for finals of 6 or more competitors -->

**Title:** Mean overlap @ 3, chance-corrected
**Higher means more agreement.**

**Sentence** (under the heading "What is mean overlap @ 3, chance-corrected? (Learn more)"):
How many of the same competitors two judges put in their top 3, averaged over every pair, with chance-level overlap set to 0.

**Scale:**
- Left: below 0 — less overlap than random
- Middle: 0 — random top 3s (sits left of centre)
- Right: 1 — same top 3s

**Caveats:**
- Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.
- The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.

## 9. Jaccard @ 3 (cc)

<!-- key: jaccard_at_3_cc · family: Top-N agreement · menu name: "Jaccard @ 3 (cc)" · charted for finals of 6 or more competitors -->

**Title:** Mean Jaccard @ 3, chance-corrected
**Higher means more agreement.**

**Sentence** (under the heading "What is mean Jaccard @ 3, chance-corrected? (Learn more)"):
The share of competitors in either judge’s top 3 that are in both, averaged over every pair, with chance-level overlap set to 0.

**Scale:**
- Left: below 0 — less overlap than random
- Middle: 0 — random top 3s (sits left of centre)
- Right: 1 — same top 3s

**Caveats:**
- Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.
- The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.

## 10. Overlap @ 3

<!-- key: overlap_at_3 · family: Top-N agreement · menu name: "Overlap @ 3" · hidden: not picked at random on load, but selectable · charted for finals of 6 or more competitors -->

**Title:** Mean overlap @ 3
**Higher means more agreement.**

**Sentence** (under the heading "What is mean overlap @ 3? (Learn more)"):
How many of the same competitors two judges put in their top 3, averaged over every pair of judges.

**Scale:**
- Left: 0 — no overlap at all
- Middle: 3/n — random top 3s (sits left of centre)
- Right: 1 — same top 3s

**Caveats:**
- Not corrected for chance. Top 3s picked at random would share 3/n on average in a final of n, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The [[overlap_at_3_cc|chance-corrected version]] subtracts this.
- Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.

## 11. Jaccard @ 3

<!-- key: jaccard_at_3 · family: Top-N agreement · menu name: "Jaccard @ 3" · hidden: not picked at random on load, but selectable · charted for finals of 6 or more competitors -->

**Title:** Mean Jaccard @ 3
**Higher means more agreement.**

**Sentence** (under the heading "What is mean Jaccard @ 3? (Learn more)"):
The share of competitors in either judge’s top 3 that are in both, averaged over every pair of judges.

**Scale:**
- Left: 0 — no overlap at all
- Middle: *(no middle point)*
- Right: 1 — same top 3s

**Caveats:**
- Not corrected for chance. Random top 3s overlap more in a smaller final, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The [[jaccard_at_3_cc|chance-corrected version]] subtracts this.
- Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.
