import { error } from '@sveltejs/kit';
import { sheet, sheets } from '#lib/server/data.js';

export function entries() {
	return sheets.map((s) => ({ id: s.id }));
}

export function load({ params }) {
	const s = sheet(params.id);
	if (!s) error(404, 'No such scoresheet');
	return { sheet: s };
}
