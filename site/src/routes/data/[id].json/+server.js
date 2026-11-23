// One scoresheet as JSON, prerendered for every scoresheet, with its percentiles, so the explorer can
// load any of them without shipping the whole dataset.
import { error } from '@sveltejs/kit';
import { profile, sheet, sheets } from '#lib/server/data.js';

export const prerender = true;

export function entries() {
	return sheets.map((s) => ({ id: s.id }));
}

export function GET({ params }) {
	const s = sheet(params.id);
	if (!s) error(404, 'No such scoresheet');
	return Response.json(profile(s));
}
