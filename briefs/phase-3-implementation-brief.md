# Phase 3: Divergence Metrics — Implementation Brief

**Script:** `scripts/compute_metrics.py`
**Input:** `data/parsed/*.json` (one file per scoresheet, schema from Phase 2)
**Output:** `data/metrics.csv` (one row per scoresheet)

Supersedes the "Phase 3" section of `plan.md`.

## Governing principle

Store **raw metric values**, plus any transform that has exactly **one defensible
form** (a deterministic re-expression of data already stored). Do **not** apply
transforms that require a choice — a chance baseline, a free parameter, a threshold,
or a null model. Those are deferred to Phase 4/5 so the choice can be made (or
varied) there without recomputing Phase 3.

Carry `num_judges` (m) and `num_competitors` (n) on every row so Phase 4/5 can
correct, normalise, and filter without re-reading the parsed files.

Computation is cheap (all metrics read the same judge × competitor rank matrix), so
store any quantity that is a free byproduct of a calculation already being run,
unless it is redundant with another stored column.

## Output columns

### Identifiers / metadata
| Column | Notes |
|---|---|
| `id` | Join key, from parsed file |
| `num_judges` | m |
| `num_competitors` | n |

Also carry through parsed metadata needed for Phase 4/5 joins (`site`, `event_name`,
`event_date`, `division_level`, `dance_format`, etc.) so `metrics.csv` is
self-sufficient.

### Concordance
| Column | Definition |
|---|---|
| `kendall_w` | Kendall's W = 12S / [m²(n³−n)], S = Σᵢ(Rᵢ − R̄)² over competitor rank-sums |
| `mean_pairwise_rho` | Mean pairwise Spearman ρ = (mW − 1)/(m − 1) |

Both are stored: they are mutually derivable, but `mean_pairwise_rho` is the more
interpretable headline and equals 0 under independent rankings for any m, whereas
raw `kendall_w` has an expected value of ≈1/m under independence and so must not be
compared across panels of different m without further treatment in Phase 4.

### Pairwise correlation / distance
| Column | Definition |
|---|---|
| `mean_pairwise_tau` | Mean Kendall's τ over all C(m,2) judge pairs. (Already 0 under independence for any m; no further correction needed.) |
| `tau_distance` | (1 − mean_pairwise_tau)/2 — fraction of competitor-pairs ordered oppositely |
| `footrule_mean` | Mean pairwise Spearman footrule, divided by its exact maximum (⌊n²/2⌋) |

`tau_distance` is a deterministic re-expression of `mean_pairwise_tau`, stored for
readability. `footrule_mean` is divided by its combinatorial maximum — a single
well-defined value, not a chance correction.

### Pairwise distribution summaries (panel-structure diagnostics)
| Column | Definition | Priority |
|---|---|---|
| `min_pairwise_tau` | Minimum τ over judge pairs | Primary |
| `sd_pairwise_tau` | SD of τ over judge pairs | Primary |
| `min_pairwise_rho` | Minimum ρ over judge pairs | Secondary |
| `sd_pairwise_rho` | SD of ρ over judge pairs | Secondary |

The τ summaries flag a single judge far from the rest of the panel (`min`) and
distinguish disagreement concentrated in a few pairs from disagreement spread evenly
(`sd`). The ρ summaries are kept only because they are free byproducts of computing
mean pairwise ρ; they occasionally differ from the τ versions (ρ weights large
displacements more heavily) but are not independently motivated. Treat them as
secondary.

Do **not** store a pairwise footrule distribution: footrule and τ-distance track
each other too closely (Diaconis–Graham inequality) for it to add anything.

### Top-N set agreement
| Column | Definition |
|---|---|
| `overlap_at_3` | Mean over judge pairs of \|A∩B\|/3 for the two top-3 sets |
| `overlap_at_5` | Mean over judge pairs of \|A∩B\|/5 for the two top-5 sets |
| `jaccard_at_3` | Mean over judge pairs of \|A∩B\|/\|A∪B\| for the two top-3 sets |
| `jaccard_at_5` | As above, top-5 |

Both N = 3 and N = 5 are stored because the choice of N is not derivable post hoc and
both are defensible (podium vs finalist tier).

For full permutations every top-N set has size exactly N, so Jaccard is a
deterministic monotone function of overlap (Jaccard = k/(2N−k) where overlap = k/N).
It is stored only as a readability re-expression and carries **no information
independent of overlap** in this setting; do not treat overlap and Jaccard agreeing
as two metrics corroborating each other.

### Rank dispersion
For each competitor, look at the spread of the m ranks it received, then average
that spread over competitors. Store three reductions of the per-competitor spread,
all free from the same pass and all raw / unnormalised:

| Column | Definition |
|---|---|
| `mean_abs_rank_dev_mean` | Per-competitor mean absolute deviation of ranks about their **mean**, averaged over competitors |
| `mean_abs_rank_dev_median` | Per-competitor mean absolute deviation of ranks about their **median**, averaged over competitors |
| `sd_rank` | Per-competitor SD of ranks, averaged over competitors |

Storing all three avoids committing to one (deviation about the mean is the standard
form; deviation about the median is more outlier-robust; `sd_rank` is the
squared-deviation cousin used for the outlier-sensitivity contrast). In all three the
per-competitor aggregation is over the m ranks; only the centre (mean vs median) or
the power (absolute vs squared) differs. The size-dependent normalisation of any
of these has multiple defensible forms and is deferred to Phase 4/5.

## Deferred to Phase 4/5 (each requires a choice)

- **Chance-corrected top-N**, e.g. (overlap − N/n)/(1 − N/n): the chance baseline is
  a modelling choice (with- vs without-replacement), so defer.
- **Comparison against a simulated null** (e.g. expressing an observed value as a
  percentile of random panels of the same m, n): depends on a null model.
- **Inclusion filtering** (e.g. ≥5 judges, ≥6 competitors): a threshold, and a
  robustness axis. Compute metrics for every scoresheet that passes Phase 2
  validity checks; filter later.
- **RBO (rank-biased overlap):** parameterised by persistence p. If wanted, compute
  later at one or more fixed p. It needs the full ordered lists, which are in
  `data/parsed/`, so nothing must be staged now to keep the option open.

## Why multiple metrics

The metrics differ in what they treat as disagreement, so running several in
parallel is deliberate:

- **Scope:** W and ρ measure panel-wide consensus; τ and footrule measure how similar
  a typical pair of judges is; top-N measures agreement on who places highest. These
  can diverge (e.g. agreement on the podium but not on lower ranks).
- **Position:** only the top-N family weights the top of the order more; W, τ, ρ,
  footrule, and the rank-dispersion columns weight all positions equally.
- **Outlier sensitivity:** squared-difference measures (ρ, `sd_rank`) amplify a single
  discordant judge; absolute-difference measures (τ-distance, footrule, the
  mean-absolute-deviation columns) are more robust. The pairwise τ summaries above
  exploit this.

Where the metrics agree, conclusions are robust to how disagreement is defined; where
they diverge, that divergence is itself a finding.
