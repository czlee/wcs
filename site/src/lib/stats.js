// Summary statistics for the charts. These match the notebook
// (notebooks/explore_metrics.ipynb): pandas mean and sem (ddof=1), and
// Plotly's default "linear" quartiles, which are numpy's default too.

const mean = (/** @type {number[]} */ xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

/** Sample standard deviation (ddof = 1). */
export function sd(/** @type {number[]} */ xs) {
	const mu = mean(xs);
	return Math.sqrt(xs.reduce((a, x) => a + (x - mu) ** 2, 0) / (xs.length - 1));
}

/**
 * The interval drawn on the bar charts. Provisional: a normal-approximation 95%
 * confidence interval for the mean, mean ± 1.96·sd/√n. Kept in one place so the
 * method can be swapped (e.g. for a t-interval or bootstrap).
 */
export const CI_LABEL = 'Mean ± 1.96 × standard error';
export function meanCI(/** @type {number[]} */ xs) {
	const mu = mean(xs);
	const half = xs.length > 1 ? (1.96 * sd(xs)) / Math.sqrt(xs.length) : NaN;
	return { n: xs.length, mean: mu, lo: mu - half, hi: mu + half };
}

/** A group with fewer scoresheets than this is drawn in grey, without an interval. */
export const MIN_CELL = 10;

/** Quantile by linear interpolation between order statistics (numpy's default, "type 7"). */
export function quantile(/** @type {number[]} */ sorted, /** @type {number} */ p) {
	const h = (sorted.length - 1) * p;
	const lo = Math.floor(h);
	return sorted[lo] + (h - lo) * ((sorted[lo + 1] ?? sorted[lo]) - sorted[lo]);
}

/** Box-plot summary: quartiles, and whiskers at the furthest data points within 1.5 × IQR of the box. */
export function boxStats(/** @type {number[]} */ xs) {
	const s = xs.toSorted((a, b) => a - b);
	const q1 = quantile(s, 0.25), med = quantile(s, 0.5), q3 = quantile(s, 0.75);
	const iqr = q3 - q1;
	const lowFence = q1 - 1.5 * iqr, highFence = q3 + 1.5 * iqr;
	const lowWhisker = s.find((x) => x >= lowFence) ?? q1;
	const highWhisker = s.findLast((x) => x <= highFence) ?? q3;
	return { n: s.length, q1, median: med, q3, lowWhisker, highWhisker };
}
