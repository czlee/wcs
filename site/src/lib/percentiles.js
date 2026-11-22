// How a scoresheet's percentile ranks (worked out in server/data.js) are put into words.
import { METRICS } from './families.js';

/** @typedef {{pct: number, of: number}} Percentile */

/** 40 → "40th", 1 → "1st", 12 → "12th". */
export function ordinal(/** @type {number} */ n) {
	const t = n % 100, u = n % 10;
	return n + (t >= 11 && t <= 13 ? 'th' : u === 1 ? 'st' : u === 2 ? 'nd' : u === 3 ? 'rd' : 'th');
}

/** "84th". */
export const rank = (/** @type {Percentile} */ p) => ordinal(Math.round(p.pct));

/** What a percentile compares against, as a sentence; `group` names the format ("Jack & Jill"). */
export function explain(/** @type {string} */ key, /** @type {Percentile} */ p, /** @type {string} */ group) {
	const r = Math.round(p.pct), minN = METRICS[key].minN;
	// A scoresheet is one of the group, so it never beats all of it (or, at the other end, none).
	const share = r >= 100 ? 'over 99%' : r <= 0 ? 'under 1%' : `${r}%`;
	return `More agreement than ${share} of all ${p.of} ${group} finals${minN ? ` with at least ${minN} competitors` : ''}, on this metric.`;
}

/** Why a metric has no percentile for a scoresheet. */
export const unranked = (/** @type {string} */ key) =>
	`Not ranked: finals with fewer than ${METRICS[key].minN} competitors are left out of this metric’s charts.`;
