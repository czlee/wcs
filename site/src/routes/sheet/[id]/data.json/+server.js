// One scoresheet as JSON, prerendered for every scoresheet, so the results pages
// can load a random example without shipping the whole dataset.
import { error, json } from '@sveltejs/kit';
import { sheet, sheets } from '#lib/server/data.js';

export const prerender = true;

export function entries() {
	return sheets.map((s) => ({ id: s.id }));
}

export function GET({ params }) {
	const s = sheet(params.id);
	if (!s) error(404, 'No such scoresheet');
	return json(s);
}
