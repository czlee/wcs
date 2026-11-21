/**
 * The twelve metrics, grouped into families of related measures. `higher` is
 * true when a higher value means the judges agree more. `minN`, where set, is the
 * smallest field a scoresheet needs to appear in that metric's charts (its value
 * is still shown on its own page). `chance` marks a metric whose 0 is chance-level
 * agreement. `hidden` keeps a metric out of the explorer's random first pick (it can
 * still be chosen by hand).
 * @type {Record<string, {key: string, label: string, short: string, higher: boolean, minN?: number, chance?: boolean, hidden?: boolean}>}
 */
export const METRICS = {
	kendall_w: { key: 'kendall_w', label: "Kendall's W", short: 'W', higher: true },
	mean_pairwise_rho: { key: 'mean_pairwise_rho', label: 'Mean pairwise Spearman ρ', short: 'ρ̄', higher: true },
	mean_pairwise_tau: { key: 'mean_pairwise_tau', label: 'Mean pairwise Kendall τ', short: 'τ̄', higher: true },
	tau_distance: { key: 'tau_distance', label: 'Kendall τ distance', short: 'τ distance', higher: false },
	footrule_mean: { key: 'footrule_mean', label: 'Mean Spearman footrule', short: 'footrule', higher: false },
	// Top 3 needs n ≥ 6 (= 2 × 3): in a final of 5, any two top-3 sets must share a competitor.
	overlap_at_3_cc: { key: 'overlap_at_3_cc', label: 'Mean overlap @ 3, chance-corrected', short: 'overlap@3 (corrected)', higher: true, minN: 6, chance: true },
	jaccard_at_3_cc: { key: 'jaccard_at_3_cc', label: 'Mean Jaccard @ 3, chance-corrected', short: 'Jaccard@3 (corrected)', higher: true, minN: 6, chance: true },
	overlap_at_3: { key: 'overlap_at_3', label: 'Mean overlap @ 3', short: 'overlap@3', higher: true, minN: 6, hidden: true },
	jaccard_at_3: { key: 'jaccard_at_3', label: 'Mean Jaccard @ 3', short: 'Jaccard@3', higher: true, minN: 6, hidden: true },
	mean_abs_rank_dev_mean: { key: 'mean_abs_rank_dev_mean', label: 'Mean abs. rank deviation from the mean', short: 'MAD (mean)', higher: false },
	mean_abs_rank_dev_median: { key: 'mean_abs_rank_dev_median', label: 'Mean abs. rank deviation from the median', short: 'MAD (median)', higher: false },
	sd_rank: { key: 'sd_rank', label: 'SD of ranks', short: 'SD', higher: false }
};

/**
 * Families, in page order. `metrics` fixes the order of every metric's values in
 * the exported data. `charts` is what the results pages show: each chart is a list
 * of variant metrics. Where a family has a `switch`, option i of that switch shows
 * variant i of every multi-variant chart in the family (the first option is the
 * default). A chart with one variant is always shown.
 * @type {{id: string, title: string, metrics: string[], charts: string[][],
 *   switch?: {label: string, options: string[]}}[]}
 */
export const FAMILIES = [
	{
		id: 'concordance', title: 'Panel-wide concordance', metrics: ['kendall_w', 'mean_pairwise_rho'],
		charts: [['kendall_w'], ['mean_pairwise_rho']]
	},
	{
		id: 'order', title: 'Distance between two judges’ rankings', metrics: ['mean_pairwise_tau', 'tau_distance', 'footrule_mean'],
		charts: [['mean_pairwise_tau', 'tau_distance'], ['footrule_mean']],
		switch: { label: 'Kendall τ or τ distance', options: ['τ̄', 'τ distance'] }
	},
	{
		id: 'top', title: 'Agreement on the top places', metrics: ['overlap_at_3_cc', 'jaccard_at_3_cc', 'overlap_at_3', 'jaccard_at_3'],
		charts: [['overlap_at_3_cc', 'overlap_at_3'], ['jaccard_at_3_cc', 'jaccard_at_3']],
		switch: { label: 'Chance correction', options: ['Corrected', 'Uncorrected'] }
	},
	{
		id: 'spread', title: 'Spread of each competitor’s ranks', metrics: ['mean_abs_rank_dev_mean', 'mean_abs_rank_dev_median', 'sd_rank'],
		charts: [['mean_abs_rank_dev_median', 'mean_abs_rank_dev_mean', 'sd_rank']],
		switch: { label: 'Measure of spread', options: ['MAD (median)', 'MAD (mean)', 'SD'] }
	}
];

export const METRIC_KEYS = FAMILIES.flatMap((f) => f.metrics);

/** The family each metric belongs to. */
export const FAMILY_OF = Object.fromEntries(FAMILIES.flatMap((f) => f.metrics.map((k) => [k, f])));
