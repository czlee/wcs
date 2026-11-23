// A JavaScript port of scripts/compute_metrics.py. Each function returns its
// intermediate values as well as the result, so the worked examples can show
// them. scripts/check-metrics.js checks allMetrics() against compute_metrics.py
// for every scoresheet on the site.
//
// R is the judge × competitor rank matrix: R[j][i] is the rank judge j gave
// competitor i. Every row is a full 1..n permutation (no ties).

/** @typedef {number[][]} Matrix */

const sum = (/** @type {number[]} */ xs) => xs.reduce((a, b) => a + b, 0);
const mean = (/** @type {number[]} */ xs) => sum(xs) / xs.length;
/** Median, averaging the middle two for an even count (as numpy does). */
export const median = (/** @type {number[]} */ xs) => {
	const s = xs.toSorted((a, b) => a - b);
	const h = s.length >> 1;
	return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};
/** Competitor i's m ranks, one per judge. */
export const column = (/** @type {Matrix} */ R, /** @type {number} */ i) => R.map((row) => row[i]);

/** Every judge pair [a, b] with a < b, in the order compute_metrics.py loops over them. */
export function judgePairs(/** @type {number} */ m) {
	/** @type {[number, number][]} */
	const out = [];
	for (let a = 0; a < m; a++) for (let b = a + 1; b < m; b++) out.push([a, b]);
	return out;
}

/** Kendall's W = 12 S / [m² (n³ − n)], with S the sum of squared deviations of rank sums from m(n+1)/2. */
export function kendallW(/** @type {Matrix} */ R) {
	const m = R.length, n = R[0].length;
	const rankSums = R[0].map((_, i) => sum(column(R, i)));
	const rBar = (m * (n + 1)) / 2;
	const devs = rankSums.map((s) => s - rBar);
	const S = sum(devs.map((d) => d * d));
	const denom = m * m * (n ** 3 - n);
	return { m, n, rankSums, rBar, devs, S, denom, W: (12 * S) / denom };
}

/** Spearman's ρ for two tie-free rankings: 1 − 6 Σd² / [n(n² − 1)]. */
export function spearman(/** @type {number[]} */ ra, /** @type {number[]} */ rb) {
	const n = ra.length;
	const d = ra.map((r, i) => r - rb[i]);
	const d2 = sum(d.map((x) => x * x));
	const denom = n * (n * n - 1);
	return { n, d, d2, denom, rho: 1 - (6 * d2) / denom };
}

/**
 * Kendall's τ for two tie-free rankings: (C − D) / C(n, 2), counting each pair of
 * competitors as concordant (both judges order them the same way) or discordant.
 * `sign[i][k]` (i < k) is +1 for concordant, −1 for discordant.
 */
export function kendallTau(/** @type {number[]} */ ra, /** @type {number[]} */ rb) {
	const n = ra.length;
	let C = 0, D = 0;
	/** @type {number[][]} */
	const sign = ra.map(() => Array(n).fill(0));
	for (let i = 0; i < n; i++)
		for (let k = i + 1; k < n; k++) {
			const s = Math.sign((ra[i] - ra[k]) * (rb[i] - rb[k]));
			sign[i][k] = sign[k][i] = s;
			if (s > 0) C++;
			else D++;
		}
	const pairs = (n * (n - 1)) / 2;
	return { n, C, D, pairs, sign, tau: (C - D) / pairs };
}

/** Spearman's footrule Σ|rank difference|, normalised by its maximum ⌊n²/2⌋. */
export function footrule(/** @type {number[]} */ ra, /** @type {number[]} */ rb) {
	const n = ra.length;
	const absDiff = ra.map((r, i) => Math.abs(r - rb[i]));
	const total = sum(absDiff);
	const max = Math.floor((n * n) / 2);
	return { n, absDiff, total, max, value: total / max };
}

/** Top-N sets (competitor indices ranked 1..N) for two judges, with overlap |A∩B|/N and Jaccard |A∩B|/|A∪B|. */
export function topN(/** @type {number[]} */ ra, /** @type {number[]} */ rb, /** @type {number} */ N) {
	const A = ra.flatMap((r, i) => (r <= N ? [i] : []));
	const B = rb.flatMap((r, i) => (r <= N ? [i] : []));
	const inter = A.filter((i) => B.includes(i));
	const union = [...new Set([...A, ...B])].sort((x, y) => x - y);
	return { N, A, B, inter, union, overlap: inter.length / N, jaccard: inter.length / union.length };
}

/** C(n, k), exactly (the values here are small). */
const comb = (/** @type {number} */ n, /** @type {number} */ k) => {
	let c = 1;
	for (let i = 1; i <= k; i++) c = (c * (n - k + i)) / i;
	return c;
};

/**
 * Expected top-N overlap and Jaccard for one judge pair by chance: each judge's top N
 * a uniformly random N of the n competitors. The number in both, i, is then
 * hypergeometric, P(i) = C(N,i) C(n−N,N−i) / C(n,N), so E[overlap] = N/n and
 * E[Jaccard] = Σ P(i) · i/(2N − i). As topn_chance in compute_metrics.py.
 */
export function topNChance(/** @type {number} */ n, /** @type {number} */ N) {
	const total = comb(n, N);
	const terms = [];
	for (let i = Math.max(0, 2 * N - n); i <= N; i++) {
		const p = (comb(N, i) * comb(n - N, N - i)) / total;
		terms.push({ i, p, jaccard: i / (2 * N - i) });
	}
	return { terms, overlap: N / n, jaccard: sum(terms.map((t) => t.p * t.jaccard)) };
}

/** (x − E)/(1 − E): 0 at chance, 1 for identical top-N sets; NaN when E = 1 (n = N). */
export const chanceCorrected = (/** @type {number} */ x, /** @type {number} */ e) => (e < 1 ? (x - e) / (1 - e) : NaN);

/** Per-competitor spread of the m ranks it received: mean |deviation| from the mean and median, and the SD (population, ddof=0). */
export function spread(/** @type {Matrix} */ R) {
	const perCompetitor = R[0].map((_, i) => {
		const ranks = column(R, i);
		const mu = mean(ranks);
		const med = median(ranks);
		const madMean = mean(ranks.map((r) => Math.abs(r - mu)));
		const madMedian = mean(ranks.map((r) => Math.abs(r - med)));
		const sd = Math.sqrt(mean(ranks.map((r) => (r - mu) ** 2)));
		return { ranks, mean: mu, median: med, madMean, madMedian, sd };
	});
	return {
		perCompetitor,
		madMean: mean(perCompetitor.map((c) => c.madMean)),
		madMedian: mean(perCompetitor.map((c) => c.madMedian)),
		sd: mean(perCompetitor.map((c) => c.sd))
	};
}

/**
 * The scales the spread metrics are normalised by, as in `rank_dispersion` in compute_metrics.py. The
 * MADs use n/4, the average spread of a panel split between one order and its exact reverse.
 * The SD uses √((n² − 1)/12), an upper bound on the average SD (and the SD of one random judge's
 * ranks). First-pass corrections for field size, to be replaced by a rigorous one.
 */
export const madScale = (/** @type {number} */ n) => n / 4;
export const sdScale = (/** @type {number} */ n) => Math.sqrt((n * n - 1) / 12);

/** Every judge pair's τ, ρ, footrule and top-3 overlap and Jaccard. */
export function pairwise(/** @type {Matrix} */ R) {
	return judgePairs(R.length).map(([a, b]) => {
		const t3 = topN(R[a], R[b], 3);
		return {
			a, b,
			tau: kendallTau(R[a], R[b]).tau,
			rho: spearman(R[a], R[b]).rho,
			footrule: footrule(R[a], R[b]).value,
			overlap3: t3.overlap, jaccard3: t3.jaccard
		};
	});
}

/** The site's twelve metrics (plus the raw spread columns they're scaled from), keyed as in data/metrics.csv. */
export function allMetrics(/** @type {Matrix} */ R) {
	const { W } = kendallW(R);
	const p = pairwise(R);
	const avg = (/** @type {string} */ k) => mean(p.map((x) => /** @type {any} */ (x)[k]));
	const tau = avg('tau');
	const s = spread(R);
	const chance3 = topNChance(R[0].length, 3);
	return {
		kendall_w: W,
		// The mean of the pairwise ρ values. compute_metrics.py instead uses the identity
		// (mW − 1)/(m − 1), which equals it exactly for tie-free rankings, so check-metrics.js
		// also checks the identity.
		mean_pairwise_rho: avg('rho'),
		mean_pairwise_tau: tau,
		tau_distance: (1 - tau) / 2,
		footrule_mean: avg('footrule'),
		overlap_at_3_cc: chanceCorrected(avg('overlap3'), chance3.overlap),
		jaccard_at_3_cc: chanceCorrected(avg('jaccard3'), chance3.jaccard),
		overlap_at_3: avg('overlap3'),
		jaccard_at_3: avg('jaccard3'),
		mean_abs_rank_dev_mean: s.madMean,
		mean_abs_rank_dev_median: s.madMedian,
		sd_rank: s.sd,
		mean_abs_rank_dev_mean_norm: s.madMean / madScale(R[0].length),
		mean_abs_rank_dev_median_norm: s.madMedian / madScale(R[0].length),
		sd_rank_norm: s.sd / sdScale(R[0].length)
	};
}

/** Largest |JS − Python| difference that still counts as a match. */
export const TOLERANCE = 1e-9;
