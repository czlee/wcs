# Choosing Metrics for Inter-Judge Disagreement in West Coast Swing Finals: A Methodological Report

## TL;DR
- For full-permutation scoresheets, run **three complementary metrics in parallel**: Kendall's W (or, better, its chance-corrected transform, mean pairwise Spearman ρ) as the omnibus concordance measure; **mean pairwise Kendall's τ-distance** as an interpretable, pair-based disagreement measure; and a **top-N agreement rate** (e.g. agreement on the podium) as a position-weighted, decision-relevant measure. Add **mean absolute rank deviation** (normalized) as a transparent, position-sensitive dispersion measure.
- The metrics differ along four axes that matter for this study: **position-weighting** (does a top-of-list swap count more than a bottom swap?), **outlier sensitivity** (one rogue judge vs. diffuse disagreement), **chance/size normalization** (is the metric comparable across different panel sizes m and field sizes n?), and **what "maximal disagreement" even means** with more than two judges.
- The single most important technical caveat: **raw Kendall's W is NOT chance-corrected** — under independent (random) rankings its expected value is approximately 1/m, not 0, so it is **not directly comparable across panels of different size**. Convert it to mean pairwise Spearman ρ (which is centered on 0 under chance) before comparing 5-judge and 9-judge panels.

## Key Findings

1. **No single number captures "disagreement."** Because the data are complete permutations from several judges, "disagreement" can mean (a) low overall concordance, (b) low average pairwise correlation, (c) churn specifically at the top of the order, or (d) large average displacement of individual competitors. These are genuinely different constructs; running several metrics is the correct design, and the *contrasts between them* are informative (e.g. high top-N agreement but low overall W means judges agree on the podium but shuffle the lower ranks).

2. **Kendall's W is the standard omnibus measure, but needs a correction for cross-panel comparison.** W ∈ [0,1] with 1 = unanimity, but its chance baseline is 1/m, not 0. The mean pairwise Spearman ρ, r̄_s = (mW − 1)/(m − 1), removes this size dependence and is the version to compare across panels.

3. **Mean pairwise Kendall's τ is the most interpretable disagreement measure** and is naturally expressed as a normalized distance (fraction of discordant pairs), which maps cleanly to "0 = identical, 1 = fully reversed" for any field size.

4. **Top-N agreement and mean absolute rank deviation supply the position-sensitivity that correlation-based measures lack.** Correlation/concordance measures (W, τ, ρ) weight a swap at ranks 1–2 the same as a swap at ranks 11–12. In a competition where placement and points hinge on the podium, that is often the wrong emphasis, so a top-N measure should be run alongside.

5. **"Maximal disagreement" is not well-defined for m > 2.** Two judges can be perfect reverses (ρ = −1). But three or more judges cannot all be mutually maximally opposed: the mean pairwise correlation is bounded below by −1/(m−1), and fully random panels sit near 0 correlation (W ≈ 1/m), not at the theoretical floor. The practical "maximum disagreement" reference for a real panel is *random/independent* rankings, not perfect reversal.

## Details

### The setting and notation
Each scoresheet has *m* judges (≈5–9) who each rank *n* competitors (≈6–12) as a complete permutation — no ties, no partial lists. We want one or more scalars per scoresheet summarizing inter-judge disagreement, to be compared across division, panel size, and field size. The full-permutation property is convenient: it removes the ties-correction and partial-list complications that dominate much of the rank-correlation literature, and it means every judge uses exactly the rank labels 1…n. Note separately that the WSDC **relative placement** system itself uses a majority/cumulative ordinal method to produce final placements — per the WSDC "Relative Placement Scoring System," a final round "must be judged by an odd number of judges: at least five, recommended seven, preferred nine," with a placement awarded once a couple has a majority of judges scoring them at or above that placement, and ties broken by the lower ordinal (rank-sum) total. The metrics below operate on the raw judge-by-competitor rank matrix, independent of how the official result is tabulated.

### Metric 1 — Kendall's coefficient of concordance (Kendall's W)

**What it measures / computation.** W is a normalized measure of the variance of the rank-sums across competitors. Let R_i be the sum of ranks competitor i receives across all m judges, and R̄ = ½m(n+1) the mean rank-sum. With S = Σ(R_i − R̄)²,

W = 12S / [m²(n³ − n)].

When judges agree, some competitors get consistently low rank-sums and others consistently high, so the rank-sums are spread out (large S, W→1). When judges disagree, rank-sums bunch toward the middle (small S, W→0). It is a normalization of the Friedman test statistic (χ² = m(n−1)W, df = n−1).

**Standard names / citations.** "Kendall's W," "coefficient of concordance." Original: Kendall, M.G. & Babington Smith, B. (Sep 1939), "The Problem of m Rankings," *The Annals of Mathematical Statistics* 10(3):275–287 (doi:10.1214/aoms/1177732186, JSTOR 2235668). Textbook: Kendall & Gibbons (1990), *Rank Correlation Methods*, 5th ed. Ties and significance testing: Legendre (2005), *J. Agric. Biol. Environ. Stat.* 10:226–245; Siegel & Castellan (1988), *Nonparametric Statistics for the Behavioral Sciences*.

**Normalization range.** [0,1], 1 = perfect agreement, 0 = the "no-overall-trend" floor. To express as *disagreement*, use 1 − W. **Crucial subtlety:** the 0 endpoint is the *minimum*, not the *chance expectation*. Under mutually independent rankings, mean pairwise Spearman ρ → 0, and since W = [(m−1)·r̄_s + 1]/m (Legendre 2022, *SAGE Encyclopedia of Research Design*), the expected W under randomness is ≈ 1/m. Practitioner sources make this explicit: "a correlation of r = 0 between 2 raters corresponds to W = 0.5, and between 3 raters to W = 0.33" — i.e., ≈0.2 for 5 judges and ≈0.11 for 9 judges. So a panel of 9 judges ranking at random produces a *smaller* W than a panel of 3 ranking at random. **This makes raw W unsafe to compare across different panel sizes.**

**Properties / sensitivities.**
- *Position-weighting:* None. W is built from rank-sums and treats a disagreement at the top identically to one at the bottom.
- *Outlier sensitivity:* Moderate and diffuse — one discordant judge among nine moves the rank-sums only slightly; W reflects aggregate, not worst-case, disagreement. This makes it robust but insensitive to a single rogue judge.
- *Behaviour at extremes:* W=1 at unanimity. W=0 only when all rank-sums are exactly equal (a specific balanced-disagreement configuration), which is *more* extreme than mere randomness.
- *Scaling:* Legendre (2005) found the classical chi-square test of W to be too conservative whenever the number of rankings m was below 20, and correctly calibrated only for 20 rankings and more; combined with E[W] ≈ 1/m, this means W's behaviour is m-dependent — so use the transform below for cross-panel comparison. Behaviour across field size n is comparatively well-normalized.

**Recommended fix:** report r̄_s = (mW − 1)/(m − 1), the **mean pairwise Spearman ρ**. It equals 0 under chance for any m and is the size-comparable quantity. (For m = 2, W = (ρ+1)/2.) Legendre notes that, unlike the mean pairwise correlation, W itself "cannot take negative values" and is one-tailed (it recognizes only positive associations), which is exactly why it is not naturally centered on a chance baseline.

**Known uses.** Sensory/consumer panel ranking (ISO 8587 ranking tests; CCFRA sensory proficiency-testing guidelines), Delphi consensus studies, and judged-sport reliability work. In DanceSport, Premelč, Vučković, James & Leskošek (2019, *Frontiers in Psychology* 10:1001) had 18 judges rate 12 couples and reported "A mean correlation of overall judging marks was 0.48. Kendall's coefficient of concordance for overall marks (W = 0.58) suggesting relatively low agreement among judges" (with ICC(2,3) = 0.62 for absolute agreement and ICC(3,3) = 0.80 for consistency) — a useful illustration that even credentialed panels can show only moderate concordance.

### Metric 2 — Mean pairwise Kendall's τ (and τ-distance)

**What it measures / computation.** For each of the C(m,2) judge pairs, compute Kendall's τ = (C − D)/C(n,2), where C and D are concordant and discordant competitor-pairs; average over all judge pairs. Equivalently, work with the **normalized Kendall τ-distance** d_τ = D / C(n,2) ∈ [0,1] = fraction of competitor-pairs the two judges order oppositely; average that over judge pairs for a clean disagreement score. τ-distance is exactly the (normalized) number of adjacent transpositions ("bubble-sort swaps") needed to turn one ranking into the other.

**Standard names / citations.** Kendall (1938), "A new measure of rank correlation," *Biometrika* 30:81–93; Kendall & Gibbons (1990). The τ-distance (Kemeny distance) is standard in social choice and rank aggregation (Diaconis & Graham 1977; Kemeny 1959).

**Normalization range.** τ ∈ [−1,+1]; τ-distance ∈ [0,1]. As disagreement: d_τ = (1−τ)/2 per pair, 0 = identical, 1 = full reversal. Averaging over pairs preserves [0,1].

**Properties / sensitivities.**
- *Position-weighting:* None (classic τ). All discordant pairs weigh equally regardless of rank position.
- *Outlier sensitivity:* Because it averages over *judge pairs*, a single discordant judge contributes to (m−1) of the C(m,2) pairs, so it is detectable but diluted. Useful contrast against W: if you also compute the *distribution* (e.g. min or variance) of pairwise τ across pairs, you can distinguish one-rogue-judge from everyone-mildly-disagrees.
- *Behaviour at extremes:* Mean τ = 1 at unanimity. For m > 2, mean τ cannot reach −1; bounded below by −1/(m−1), and random panels sit near 0.
- *Scaling:* The per-pair normalization by C(n,2) makes τ-distance comparable across field sizes n. Averaging over judge pairs normalizes across panel size m, and the chance level is 0 for all m — so mean pairwise τ is **better-behaved for cross-panel comparison than raw W**.

**Known uses.** Ubiquitous in comparing ranked lists; used pairwise between judges/assessors in sensory science, peer grading, and machine-evaluation studies. (Note: reported magnitudes of pairwise τ between human assessors vary enormously by domain — from strong agreement on clean, low-dimensional ranking tasks down to near-zero on noisy subjective tasks — so do not import an "expected" τ from another field; calibrate against your own data and simulated null.)

### Metric 3 — Top-N agreement rate

**What it measures / computation.** A family of position-focused measures restricted to the top N of each ranking (e.g. N=3 podium, or N=5). Common forms:
- *Top-N set overlap (Jaccard or overlap@N):* for a judge pair, |Top_N(A) ∩ Top_N(B)| / N (overlap) or / |union| (Jaccard); average over judge pairs.
- *Consensus top-N agreement:* fraction of judges who place a given competitor in their top N, or whether the panel-consensus top-N set is unanimous.
- *Rank-biased overlap (RBO)* and *AP-correlation* (τ_AP): top-weighted similarity measures with geometric/positional decay, designed precisely so that swaps near the top cost more than swaps deeper down.

**Standard names / citations.** Precision@k / overlap@k and Jaccard@k are standard in information retrieval and recommender evaluation. RBO: Webber, Moffat & Zobel (2010), "A similarity measure for indefinite rankings," *ACM TOIS*. AP-correlation: Yilmaz, Aslam & Robertson (2008). Top-weighted τ variants: Vigna (2015); Kumar & Vassilvitskii (2010).

**Normalization range.** Overlap@N and Jaccard@N ∈ [0,1], 1 = identical top-N set. RBO ∈ [0,1]. As disagreement, use 1 − (the similarity).

**Properties / sensitivities.**
- *Position-weighting:* **This is the whole point** — top-N (and especially RBO/τ_AP) explicitly privileges the top of the order. This is the only family among the candidates that does so, and it is the most decision-relevant for a competition where podium and points are what matter.
- *Outlier sensitivity:* Set-overlap@N is coarse — it ignores *where* inside the top N items sit and ignores everything below N — so it can be noisy/granular for small N (e.g. N=3 with 6 competitors). RBO/τ_AP degrade more gracefully.
- *Behaviour at extremes:* 1 when top-N sets coincide; floor depends on N and n. A pure top-N set-overlap can be 0 (disjoint top-N sets) even when the lower order is similar — a sharp cutoff effect to be aware of.
- *Scaling:* Set-overlap@N has a discrete, low-resolution range when N is small (only N+1 possible values for overlap@N), and its chance baseline depends on both N and n, so chance-correct (or at least hold N fixed) when comparing across field sizes. RBO needs a tunable persistence parameter p.

**Known uses.** Standard in IR/recommender evaluation; RBO widely used to compare search-engine and recommender rankings, and in network science and neuroscience. The top-weighting rationale (top results matter most) is explicitly the motivation in that literature.

### Metric 4 — Mean absolute rank deviation across judges

**What it measures / computation.** For each competitor i, compute the spread of the m ranks it received — e.g. the mean absolute deviation of competitor i's ranks about their mean (or median) rank — then average over the n competitors. A natural normalized form divides by the maximum possible mean absolute deviation so the score lands in [0,1]. This is the "average deviation (AD)" interrater-agreement index applied to ranks.

**Standard names / citations.** Average deviation index, ADM / ADMd (Burke & Dunlap 2002; Burke, Finkelstein & Dusig 1999). Closely related: the per-competitor standard deviation of ranks (used in figure-skating and gymnastics judging analyses) and Spearman's footrule when expressed pairwise.

**Normalization range.** Raw, it is in rank units (0 = all judges agree exactly on every competitor's rank). Normalized by its maximum it is [0,1]; as an agreement measure use 1 − normalized.

**Properties / sensitivities.**
- *Position-weighting:* None by default — a 3-rank spread at the top counts the same as at the bottom. (It *can* be made position-weighted by weighting competitors by their mean rank, but that departs from the standard measure.)
- *Outlier sensitivity:* Absolute deviation is **more robust to a single rogue judge** than a variance/SD-based measure (which squares deviations). This is a deliberate, useful contrast: run the SD-of-ranks version alongside and the gap between them flags whether disagreement is driven by one extreme judge.
- *Behaviour at extremes:* 0 at unanimity. Maximum when each competitor's ranks are maximally spread across judges.
- *Scaling:* The raw measure grows with n (more competitors → larger possible rank gaps), so it **must be normalized by its n-dependent maximum** to compare across field sizes. Averaging across competitors normalizes the per-competitor contributions; the dependence on m is mild but the maximum spread also depends on m, so normalize accordingly.

**Known uses.** Average-deviation interrater indices are standard in organizational/I-O psychology. Per-competitor rank/score dispersion (SD, mean absolute deviation) is the workhorse in empirical figure-skating and gymnastics judging studies. For example, Leskošek, Čuk et al. ("Is the Quality of Judging in Women Artistic Gymnastics Equivalent at Major Competitions of Different Levels?", PMC3796836; 6 judges per apparatus, Berlin 2011 vs. Universiade 2009) report that "average deviations of judges from the final E score were close to zero (p=0.84)," using mean and mean-absolute deviations of judges from the panel score as the core reliability measures; a companion 2024 Paris breakdancing analysis reports the largest individual-judge average absolute deviation at 0.34 point and the largest mean rank deviation at 0.88.

### Two strong additional candidates

**Spearman's ρ (and mean pairwise ρ).** Mean pairwise Spearman ρ is, as noted, algebraically equivalent to the chance-corrected W, so it adds little *new* if you already report r̄_s — but it is the natural, size-comparable headline number and the most familiar to readers. ρ uses *squared* rank differences, so unlike τ it **mildly emphasizes large displacements** and is more outlier-sensitive than τ; the ρ-vs-τ contrast is itself informative. Cite Spearman (1904).

**Spearman's footrule distance.** F = Σ_i |r_A(i) − r_B(i)|, the sum of absolute rank displacements between two judges; average over judge pairs and normalize by its maximum (⌊n²/2⌋ for even n) to get [0,1]. It is a true metric on permutations, robust to outliers (absolute, not squared), and bounded by Kendall's τ-distance via the Diaconis–Graham inequality d_τ ≤ F ≤ 2·d_τ (so footrule and τ-distance induce the same topology and rarely disagree qualitatively). It is essentially the pairwise sibling of mean absolute rank deviation and a clean, citable alternative. Cite Diaconis & Graham (1977), "Spearman's footrule as a measure of disarray," *JRSS-B* 39:262–268.

**Intraclass Correlation Coefficient (ICC) on ranks — use with caution.** ICC (Shrout & Fleiss 1979; McGraw & Wong 1996) is the dominant inter-rater reliability measure for *continuous/ordinal scores*. Applied to ranks, ICC(2,k)/ICC(3,k) is closely related to Kendall's W and mean ρ. But several authoritative practitioners explicitly warn that ICC is intended for ratings, not ranks; because every judge here uses the identical set of labels 1…n, the rater main-effect and "absolute agreement vs consistency" distinction that gives ICC its value largely collapses (every judge has the same mean and variance of ranks by construction). The DanceSport study above is instructive: it reported ICC(3,3) consistency (0.80) much higher than ICC(2,3) absolute agreement (0.62) — a gap that is meaningful for *scores* but largely artefactual for forced permutations. **Recommendation: ICC adds little over W/ρ in the pure-permutation setting and risks reviewer objections; prefer the rank-native measures.** Mention it only to pre-empt the question.

### The dimensions along which the metrics differ (the core of the report)

The reason to run several metrics is that each "cares about" something different:

1. **Aggregate vs. pairwise vs. positional construct.** W asks "is there a shared signal across the whole panel?" (variance of consensus). Mean pairwise τ/ρ/footrule ask "how similar is a typical pair of judges?" Top-N asks "do they agree on who's at the top?" These can diverge sharply (agree on podium, disagree below → high top-N, low W).

2. **Position-weighting.** Only the top-N / RBO / τ_AP family weights the top of the order more. W, τ, ρ, footrule, and mean absolute deviation are all position-flat. For a competition with podium/points stakes, include at least one top-weighted metric.

3. **Outlier (one-rogue-judge) sensitivity.** Squared-deviation measures (ρ, SD-of-ranks) amplify a single extreme judge; absolute-deviation measures (τ-distance, footrule, mean absolute rank deviation) are more robust. Reporting a robust and a non-robust measure, and looking at their gap, is a cheap rogue-judge detector. The *distribution* of pairwise τ (not just its mean) is the most direct rogue-judge diagnostic.

4. **Chance/size normalization (comparability across panels).** This is the make-or-break dimension for this study because panel size m and field size n vary across scoresheets. Raw W has a chance baseline of 1/m → not comparable. Mean pairwise τ and ρ have chance baseline 0 for all m → comparable. Distance measures normalized by their n-dependent maxima (τ-distance, normalized footrule, normalized mean absolute deviation) are comparable across n. **Never compare raw, unnormalized values across different m or n.**

5. **Meaning of the "disagreement" endpoint.** For m > 2 there is no configuration where all judges mutually reverse each other; mean pairwise correlation is floored at −1/(m−1) (a consequence of the positive-semidefiniteness of any correlation matrix), and the realistic "maximum disagreement" benchmark is independent/random ranking (mean correlation ≈ 0, W ≈ 1/m), not −1 or 0. Define your disagreement scale against the *random* benchmark, ideally by simulating random panels of the same (m, n) and reporting where the observed value sits.

### Summary comparison matrix

| Metric | Range (agreement) | As disagreement | Position-weighted? | Outlier (rogue-judge) sensitivity | Chance baseline | Comparable across m? | Comparable across n? |
|---|---|---|---|---|---|---|---|
| **Kendall's W** | [0,1], 1=unanimity | 1−W | No | Low (diffuse, aggregate) | **≈1/m (NOT 0)** | **No (raw)** | Yes (well-normalized) |
| **Mean pairwise Spearman ρ** = (mW−1)/(m−1) | [−1/(m−1), 1] | 1−ρ̄ | No | Medium (squares Δ) | 0 for all m | **Yes** | Yes |
| **Mean pairwise Kendall τ / τ-distance** | τ∈[−1/(m−1),1]; d_τ∈[0,1] | d_τ=(1−τ)/2 | No | Medium-low (robust) | 0 for all m | **Yes** | Yes (÷C(n,2)) |
| **Top-N overlap / RBO** | [0,1] | 1−overlap | **Yes (the point)** | Coarse/granular for small N | depends on N,n | hold N fixed | hold N fixed; chance-correct |
| **Mean absolute rank deviation** | rank units; [0,1] normed | 1−norm | No | **Low (robust, absolute)** | depends on m,n | normalize by max | **must normalize by n-dep max** |
| **Spearman footrule (pairwise)** | [0,1] normed | F/F_max | No | Low (robust, absolute) | depends on n | yes (averaged) | yes (÷⌊n²/2⌋) |
| **ICC(2,k)/(3,k) on ranks** | ~[0,1] | 1−ICC | No | Medium | ~0 | partial | partial — *not recommended for permutations* |

## Recommendations

**Primary panel of metrics (compute all four per scoresheet):**
1. **Mean pairwise Spearman ρ** (equivalently chance-corrected W via r̄_s = (mW−1)/(m−1)) — headline omnibus agreement, comparable across m. Report 1 − r̄_s as disagreement.
2. **Mean pairwise Kendall τ-distance** — interpretable per-pair disagreement, comparable across m and n; also keep the **distribution** of pairwise τ (min, SD) as a rogue-judge diagnostic.
3. **Top-3 (podium) agreement** — overlap@3 averaged over judge pairs, or RBO with a stated p, for decision-relevant top-weighting.
4. **Normalized mean absolute rank deviation** — transparent, robust, position-flat dispersion; pair it with SD-of-ranks to expose outlier-driven disagreement.

**Staged plan:**
- *Stage 1 (build & validate):* Compute all four on every scoresheet. For each (m, n) combination present in the data, simulate ~10,000 random panels to get the chance distribution of each metric; express observed values as deviations from (or percentiles within) that null. This solves the cross-panel comparability problem empirically regardless of analytic normalization.
- *Stage 2 (analyze):* Compare each metric across division level, panel size, and field size. **Benchmark that should change your approach:** if the four metrics are highly correlated across scoresheets (Spearman ρ between metric-series > ~0.9), collapse to one headline (mean pairwise ρ) plus top-3 agreement; if they diverge (correlation < ~0.7), keep all four because they are capturing distinct phenomena — which is itself a finding worth reporting.
- *Stage 3 (report):* Lead with mean pairwise ρ and top-3 agreement; use footrule/mean-absolute-deviation and the pairwise-τ distribution as robustness and diagnostic supports.

**Thresholds:** Treat r̄_s ≥ 0.7 as strong panel consensus, 0.3–0.5 as moderate, and a value near the simulated chance level as effectively random. Flag any scoresheet where a robust and a non-robust metric disagree markedly as a candidate one-rogue-judge case for manual inspection.

**Avoid:** raw Kendall's W for cross-panel comparison; ICC on pure rank permutations; any unnormalized distance compared across different field sizes; and treating "perfect reversal" as the disagreement ceiling for m > 2.

## Caveats
- **W's chance baseline (≈1/m) is the most consequential and most overlooked issue.** Many tutorial sources loosely call the null "W = 0," conflating the *minimum* of W with its *expected value under randomness*; the rigorous statement is E[W] → 1/m via the exact W↔r̄_s algebra (Legendre 2022). Use r̄_s or simulation, not raw W, across panels of different size.
- The **−1/(m−1) lower bound** on mean pairwise correlation rests on the positive-semidefiniteness of correlation matrices (a standard linear-algebra fact); cite that underlying fact if a formal reference is required, as the cleanest expository proofs are not always in textbooks.
- **Top-N set-overlap is low-resolution for small N and small fields** (few discrete values; sharp cutoff ignoring near-misses just outside N). Prefer RBO or a graded top-weighted measure if this granularity is a problem, and always hold N fixed when comparing.
- The **ICC-on-ranks** literature is genuinely divided; the position taken here (avoid it for pure permutations) is a judgment call, defensible but not unanimous.
- Empirical agreement figures cited from other judged domains (DanceSport W = 0.58, mean overall-mark correlation 0.48; figure-skating/gymnastics dispersion studies) are **context references, not benchmarks for West Coast Swing**; WCS panels differ in size, training, and criteria, so calibrate expectations against your own simulated null and observed distribution. Pairwise-correlation magnitudes between human raters vary so widely across task types that no single "expected" value should be imported.
- This report deliberately constrains itself to the **full-ranking** setting; if any scoresheets contain ties or incomplete rankings, the ties-corrected forms of W and τ and the partial-list machinery of RBO would need to be reintroduced.