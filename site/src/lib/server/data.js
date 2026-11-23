// Build-time access to the exported data (scripts/export_site_data.py). Only
// server load functions import this, so the full dataset never ships to the
// browser: pages get just what they show.
import sheetsJson from '#lib/data/sheets.json';
import exportInfo from '#lib/data/export.json';
import { METRICS, METRIC_KEYS } from '#lib/families.js';
import { regionOf } from '#lib/regions.js';

/**
 * @typedef {{id: string, format: string, level: string, event: string, date: string, name: string,
 *   country: string | null, state: string | null, site: string, url: string, judges: string[], competitors: string[], R: number[][],
 *   py: Record<string, number>}} Sheet
 * @typedef {Sheet & {percentiles: Record<string, import('#lib/percentiles.js').Percentile>}} Profile
 */

/** @type {Sheet[]} */
export const sheets = /** @type {any} */ (sheetsJson);
export const info = exportInfo;
const byId = new Map(sheets.map((s) => [s.id, s]));

// A country in no region would silently drop out of every view with a region filter.
const unplaced = new Set(sheets.filter((s) => !regionOf(s.country)).map((s) => s.country ?? `none (${s.event})`));
if (unplaced.size) throw new Error(`Countries in no region (lib/regions.js): ${[...unplaced].join(', ')}`);

/** One scoresheet, in full. */
export const sheet = (/** @type {string} */ id) => byId.get(id);

/** A short description of a scoresheet for lists, tooltips and the chart points. */
export const summary = (/** @type {Sheet} */ s) => ({
	id: s.id, format: s.format, level: s.level, event: s.event, date: s.date, name: s.name,
	country: s.country, state: s.state, m: s.judges.length, n: s.competitors.length
});

/**
 * Chart data for one format: each scoresheet's level, label and metric values,
 * rounded to 6 decimal places (plenty for the charts; the worked examples
 * recompute exact values). A value is null where the field is smaller than the
 * metric's `minN`, which leaves that scoresheet out of that metric's charts.
 */
export function chartRows(/** @type {string} */ format) {
	return sheets
		.filter((s) => s.format === format)
		.map((s) => ({
			...summary(s),
			v: METRIC_KEYS.map((k) =>
				s.competitors.length < (METRICS[k].minN ?? 0) ? null : Math.round(s.py[k] * 1e6) / 1e6)
		}));
}

/**
 * A fixed scoresheet to show before the page picks a random one (and when
 * JavaScript is off): the first, by date, with a typical panel and field size.
 */
export function fallbackSheet(/** @type {string} */ format) {
	return /** @type {Sheet} */ (
		sheets.find((s) => s.format === format && s.judges.length === 5 && s.competitors.length === 10) ??
			sheets.find((s) => s.format === format)
	);
}

/** Whether a scoresheet's field is big enough for it to count for a metric (its `minN`). */
const counts = (/** @type {Sheet} */ s, /** @type {string} */ k) => s.competitors.length >= (METRICS[k].minN ?? 0);

/**
 * For each format and metric, the precomputed values of the scoresheets
 * that appear in that metric's charts, oriented so that larger means more
 * agreement and sorted ascending.
 * @type {Map<string, number[]>}
 */
const groups = new Map();
for (const s of sheets) {
	for (const k of METRIC_KEYS) {
		if (!counts(s, k)) continue;
		const key = `${s.format}/${k}`;
		if (!groups.has(key)) groups.set(key, []);
		groups.get(key)?.push(METRICS[k].higher ? s.py[k] : -s.py[k]);
	}
}
for (const g of groups.values()) g.sort((a, b) => a - b);

/** Index of the first element of sorted `a` that is ≥ x (or > x if `strict`). */
function bisect(/** @type {number[]} */ a, /** @type {number} */ x, strict = false) {
	let lo = 0, hi = a.length;
	while (lo < hi) {
		const mid = (lo + hi) >> 1;
		if (strict ? a[mid] <= x : a[mid] < x) lo = mid + 1;
		else hi = mid;
	}
	return lo;
}

/**
 * A scoresheet's percentile rank for each metric among the scoresheets of the same
 * format (at every level), from the precomputed values: 100 is the most agreement,
 * whichever direction the metric runs. Ties take the mid-rank: the percentage of
 * the group with less agreement, plus half of those tied with it (itself
 * included). Values within 1e-9 count as tied, so floating-point noise doesn't
 * split ties. A metric is missing where the scoresheet is left out of its charts.
 * @returns {Record<string, import('#lib/percentiles.js').Percentile>}
 */
export function percentiles(/** @type {Sheet} */ s) {
	/** @type {Record<string, import('#lib/percentiles.js').Percentile>} */
	const out = {};
	for (const k of METRIC_KEYS) {
		const g = groups.get(`${s.format}/${k}`);
		if (!g || !counts(s, k)) continue;
		const x = METRICS[k].higher ? s.py[k] : -s.py[k];
		const below = bisect(g, x - 1e-9);
		const tied = bisect(g, x + 1e-9, true) - below;
		out[k] = { pct: (100 * (below + tied / 2)) / g.length, of: g.length };
	}
	return out;
}

/**
 * A scoresheet with its percentiles: what the explorer's dialogs show.
 * @returns {Profile}
 */
export const profile = (/** @type {Sheet} */ s) => ({ ...s, percentiles: percentiles(s) });
