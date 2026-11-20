// Build-time access to the exported data (scripts/export_site_data.py). Only
// server load functions import this, so the full dataset never ships to the
// browser: pages get just what they show.
import sheetsJson from '#lib/data/sheets.json';
import exportInfo from '#lib/data/export.json';
import { METRICS, METRIC_KEYS } from '#lib/families.js';

/**
 * @typedef {{id: string, format: string, level: string, event: string, date: string, name: string,
 *   site: string, url: string, judges: string[], competitors: string[], R: number[][],
 *   py: Record<string, number>}} Sheet
 */

/** @type {Sheet[]} */
export const sheets = /** @type {any} */ (sheetsJson);
export const info = exportInfo;
const byId = new Map(sheets.map((s) => [s.id, s]));

/** One scoresheet, in full. */
export const sheet = (/** @type {string} */ id) => byId.get(id);

/** A short description of a scoresheet for lists, tooltips and the chart points. */
export const summary = (/** @type {Sheet} */ s) => ({
	id: s.id, format: s.format, level: s.level, event: s.event, date: s.date, name: s.name,
	m: s.judges.length, n: s.competitors.length
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
