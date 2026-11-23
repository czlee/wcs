/**
 * Dimensions of a scoresheet, for filtering (and later, for grouping the x-axis and
 * colouring points). Each one sorts scoresheets into an ordered list of bins. This is
 * plain definitions, safe to import in the browser: keep it free of lib/server imports.
 *
 * A dimension with a `range` is filtered by a slider from `min` to `max`, whose top stop
 * takes in everything above it too; the others are filtered by choosing bins.
 *
 * `id` is also the dimension's URL parameter, and a bin's `id` its value there, so both
 * must stay stable and avoid commas and plus signs. `of` takes a chart row or list entry
 * (anything with `m` judges, `n` competitors and a `country`). Bins are exclusive, but needn't cover every
 * value: a scoresheet in no bin shows only while that dimension has no filter.
 * @typedef {{m: number, n: number, country: string | null}} Countable
 * @typedef {{id: string, label: string, test: (v: any) => boolean}} Bin
 * @typedef {{id: string, label: string, tip?: string, of: (r: Countable) => any, bins: Bin[],
 *   range?: {min: number, max: number}}} Dimension
 */
import { REGIONS, regionOf } from './regions.js';

/** @type {Dimension[]} */
export const DIMENSIONS = [
	{
		id: 'finalists', label: 'Finalists', of: (r) => r.n,
		tip: 'The number of couples in the final. Some metrics depend on field size, so narrowing this range can help take that variable out of the comparison.',
		// Very few finals have more than 16.
		range: { min: 5, max: 16 },
		bins: [
			{ id: '5', label: '5', test: (v) => v <= 5 },
			{ id: '6-7', label: '6–7', test: (v) => v >= 6 && v <= 7 },
			{ id: '8-10', label: '8–10', test: (v) => v >= 8 && v <= 10 },
			{ id: '11-13', label: '11–13', test: (v) => v >= 11 && v <= 13 },
			{ id: '14-up', label: '14+', test: (v) => v >= 14 }
		]
	},
	{
		id: 'judges', label: 'Judges', of: (r) => r.m,
		bins: [
			{ id: '5', label: '5', test: (v) => v === 5 },
			{ id: '7', label: '7', test: (v) => v === 7 },
			{ id: '9', label: '9', test: (v) => v === 9 }
		]
	},
	{
		id: 'region', label: 'Region', of: (r) => regionOf(r.country),
		bins: REGIONS.map(({ id, label }) => ({ id, label, test: (v) => v === id }))
	}
];

/**
 * What's chosen in each dimension, by dimension id: bin ids, or a range's [low, high]
 * (both inclusive). Empty means no filter.
 * @typedef {Record<string, any[]>} Filters
 */

/** @returns {Filters} */
export const noFilters = () => Object.fromEntries(DIMENSIONS.map((d) => [d.id, []]));

export const anyFilters = (/** @type {Filters} */ filters) => DIMENSIONS.some((d) => filters[d.id]?.length > 0);

/** The id of the bin a scoresheet falls in, if any. */
export const categoryOf = (/** @type {Dimension} */ dim, /** @type {Countable} */ row) =>
	dim.bins.find((b) => b.test(dim.of(row)))?.id;

/** A range's ends, which are the slider's own if nothing is chosen. */
export const rangeOf = (/** @type {Dimension} */ d, /** @type {Filters} */ filters) => {
	const { min, max } = /** @type {{min: number, max: number}} */ (d.range);
	const [lo, hi] = filters[d.id]?.length ? filters[d.id] : [min, max];
	return { min, max, lo, hi };
};

/** The choice a range stands for: none if it spans the whole slider. */
export const rangeChoice = (/** @type {Dimension} */ d, /** @type {number} */ lo, /** @type {number} */ hi) =>
	lo <= /** @type {any} */ (d.range).min && hi >= /** @type {any} */ (d.range).max ? [] : [lo, hi];

/** Whether a scoresheet is among what's chosen in every dimension that has a choice. */
export const matches = (/** @type {Countable} */ row, /** @type {Filters} */ filters) =>
	DIMENSIONS.every((d) => {
		const chosen = filters[d.id];
		if (!chosen?.length) return true;
		if (d.range) {
			const { min, max, lo, hi } = rangeOf(d, filters);
			const v = Math.min(Math.max(d.of(row), min), max);
			return v >= lo && v <= hi;
		}
		return chosen.includes(/** @type {string} */ (categoryOf(d, row)));
	});

/** A range as a URL value: "8-10", or "14-up" where it's open-ended. */
const rangeParam = (/** @type {Dimension} */ d, /** @type {number[]} */ [lo, hi]) =>
	hi >= /** @type {any} */ (d.range).max ? `${lo}-up` : `${lo}-${hi}`;

function parseRange(/** @type {Dimension} */ d, /** @type {string} */ s) {
	const { min, max } = /** @type {{min: number, max: number}} */ (d.range);
	const found = s.match(/^(\d+)-(\d+|up)$/);
	if (!found) return [];
	const clamp = (/** @type {number} */ v) => Math.min(Math.max(v, min), max);
	const lo = clamp(+found[1]), hi = found[2] === 'up' ? max : clamp(+found[2]);
	return lo > hi ? [] : rangeChoice(d, lo, hi);
}

/** Filters from a URL's parameters; anything unrecognised is ignored. */
export function filtersFromParams(/** @type {URLSearchParams} */ params) {
	return /** @type {Filters} */ (Object.fromEntries(DIMENSIONS.map((d) => {
		if (d.range) return [d.id, parseRange(d, params.get(d.id) ?? '')];
		const asked = (params.get(d.id) ?? '').split(',');
		return [d.id, d.bins.map((b) => b.id).filter((id) => asked.includes(id))];
	})));
}

/** Write filters into a URL's parameters (in place), dropping empty ones. */
export function setFilterParams(/** @type {URLSearchParams} */ params, /** @type {Filters} */ filters) {
	for (const d of DIMENSIONS) {
		if (filters[d.id]?.length) params.set(d.id, d.range ? rangeParam(d, filters[d.id]) : filters[d.id].join(','));
		else params.delete(d.id);
	}
	return params;
}

/** A query string with readable commas ("judges=5,7"). */
export const queryString = (/** @type {URLSearchParams} */ params) => params.toString().replaceAll('%2C', ',');
