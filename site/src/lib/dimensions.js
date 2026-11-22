/**
 * Dimensions of a scoresheet, for filtering (and later, for grouping the x-axis and
 * colouring points). Each one sorts scoresheets into an ordered list of bins. This is
 * plain definitions, safe to import in the browser: keep it free of lib/server imports.
 *
 * `id` is also the dimension's URL parameter, and a bin's `id` its value there, so both
 * must stay stable and avoid commas and plus signs. `of` takes a chart row or list entry
 * (anything with `m` judges and `n` competitors). Bins are exclusive, but needn't cover every
 * value: a scoresheet in no bin shows only while that dimension has no filter.
 * @typedef {{m: number, n: number}} Countable
 * @typedef {{id: string, label: string, test: (v: number) => boolean}} Bin
 * @typedef {{id: string, label: string, tip?: string, of: (r: Countable) => number, bins: Bin[]}} Dimension
 */

/** @type {Dimension[]} */
export const DIMENSIONS = [
	{
		id: 'finalists', label: 'Finalists', of: (r) => r.n,
		tip: 'The number of couples in the final.',
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
	}
];

/** The bins chosen in each dimension, by dimension id. None chosen means no filter. */
/** @typedef {Record<string, string[]>} Filters */

/** @returns {Filters} */
export const noFilters = () => Object.fromEntries(DIMENSIONS.map((d) => [d.id, []]));

export const anyFilters = (/** @type {Filters} */ filters) => DIMENSIONS.some((d) => filters[d.id]?.length > 0);

/** The id of the bin a scoresheet falls in, if any. */
export const categoryOf = (/** @type {Dimension} */ dim, /** @type {Countable} */ row) =>
	dim.bins.find((b) => b.test(dim.of(row)))?.id;

/** Whether a scoresheet is in a chosen bin of every dimension that has any chosen. */
export const matches = (/** @type {Countable} */ row, /** @type {Filters} */ filters) =>
	DIMENSIONS.every((d) => {
		const chosen = filters[d.id];
		return !chosen?.length || chosen.includes(/** @type {string} */ (categoryOf(d, row)));
	});

/** Filters from a URL's parameters; unknown bins are ignored. */
export function filtersFromParams(/** @type {URLSearchParams} */ params) {
	return /** @type {Filters} */ (Object.fromEntries(DIMENSIONS.map((d) => {
		const asked = (params.get(d.id) ?? '').split(',');
		return [d.id, d.bins.map((b) => b.id).filter((id) => asked.includes(id))];
	})));
}

/** Write filters into a URL's parameters (in place), dropping empty ones. */
export function setFilterParams(/** @type {URLSearchParams} */ params, /** @type {Filters} */ filters) {
	for (const d of DIMENSIONS) {
		if (filters[d.id]?.length) params.set(d.id, filters[d.id].join(','));
		else params.delete(d.id);
	}
	return params;
}

/** A query string with readable commas ("finalists=8-10,11-13"). */
export const queryString = (/** @type {URLSearchParams} */ params) => params.toString().replaceAll('%2C', ',');
