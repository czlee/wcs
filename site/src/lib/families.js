/**
 * The twelve metrics, grouped into families of related measures. `higher` is
 * true when a higher value means the judges agree more.
 * @type {Record<string, {key: string, label: string, short: string, higher: boolean}>}
 */
export const METRICS = {
	kendall_w: { key: 'kendall_w', label: "Kendall's W", short: 'W', higher: true },
	mean_pairwise_rho: { key: 'mean_pairwise_rho', label: 'Mean pairwise Spearman ρ', short: 'ρ̄', higher: true },
	mean_pairwise_tau: { key: 'mean_pairwise_tau', label: 'Mean pairwise Kendall τ', short: 'τ̄', higher: true },
	tau_distance: { key: 'tau_distance', label: 'Kendall τ distance', short: 'τ distance', higher: false },
	footrule_mean: { key: 'footrule_mean', label: 'Mean Spearman footrule', short: 'footrule', higher: false },
	overlap_at_3: { key: 'overlap_at_3', label: 'Mean overlap @ 3', short: 'overlap@3', higher: true },
	jaccard_at_3: { key: 'jaccard_at_3', label: 'Mean Jaccard @ 3', short: 'Jaccard@3', higher: true },
	overlap_at_5: { key: 'overlap_at_5', label: 'Mean overlap @ 5', short: 'overlap@5', higher: true },
	jaccard_at_5: { key: 'jaccard_at_5', label: 'Mean Jaccard @ 5', short: 'Jaccard@5', higher: true },
	mean_abs_rank_dev_mean: { key: 'mean_abs_rank_dev_mean', label: 'Mean abs. rank deviation from the mean', short: 'MAD (mean)', higher: false },
	mean_abs_rank_dev_median: { key: 'mean_abs_rank_dev_median', label: 'Mean abs. rank deviation from the median', short: 'MAD (median)', higher: false },
	sd_rank: { key: 'sd_rank', label: 'SD of ranks', short: 'SD', higher: false }
};

/** Families, in page order. */
export const FAMILIES = [
	{ id: 'concordance', title: 'Whole-panel concordance', metrics: ['kendall_w', 'mean_pairwise_rho'] },
	{ id: 'order', title: 'Pairwise ordering', metrics: ['mean_pairwise_tau', 'tau_distance', 'footrule_mean'] },
	{ id: 'top', title: 'Agreement on the top places', metrics: ['overlap_at_3', 'jaccard_at_3', 'overlap_at_5', 'jaccard_at_5'] },
	{ id: 'spread', title: 'Spread of each competitor’s ranks', metrics: ['mean_abs_rank_dev_mean', 'mean_abs_rank_dev_median', 'sd_rank'] }
];

export const METRIC_KEYS = FAMILIES.flatMap((f) => f.metrics);
