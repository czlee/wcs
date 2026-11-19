import { sheets, summary } from '#lib/server/data.js';

export function load() {
	return { list: sheets.map(summary) };
}
