/**
 * What the explorer is showing, as its URL's parameters: the metric, the filters (see
 * dimensions.js), the highlighted scoresheet and the open dialog. The values are in links
 * people share, so keep them stable.
 */
import { filtersFromParams, queryString, setFilterParams } from './dimensions.js';
import { METRICS } from './families.js';

/** @typedef {'working' | 'profile' | 'limitations' | 'about'} Dialog */
/**
 * `metric`, `sheet` and `dialog` are null where the URL doesn't say.
 * @typedef {{metric: string | null, filters: import('./dimensions.js').Filters, sheet: string | null, dialog: Dialog | null}} View
 */

/** @type {Dialog[]} */
export const DIALOGS = ['working', 'profile', 'limitations', 'about'];
/** Whether a dialog is about the highlighted scoresheet, so that a link to it must say which one. */
export const aboutSheet = (/** @type {Dialog | null} */ d) => d === 'working' || d === 'profile';

/** The view a URL's query asks for; anything unrecognised is ignored. @returns {View} */
export function parseView(/** @type {string} */ search) {
	const p = new URLSearchParams(search);
	const metric = p.get('metric'), dialog = /** @type {Dialog} */ (p.get('dialog'));
	return {
		metric: metric && Object.hasOwn(METRICS, metric) ? metric : null,
		filters: filtersFromParams(p),
		sheet: p.get('sheet') || null,
		dialog: DIALOGS.includes(dialog) ? dialog : null
	};
}

/** A view as a query, starting with "?". Other parameters in `search`, the current query, are kept. */
export function viewQuery(/** @type {View} */ view, search = '') {
	const p = new URLSearchParams(search);
	setFilterParams(p, view.filters);
	for (const k of /** @type {const} */ (['metric', 'sheet', 'dialog'])) {
		const v = view[k];
		if (v) p.set(k, v);
		else p.delete(k);
	}
	return `?${queryString(p)}`;
}
