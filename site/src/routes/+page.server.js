import { chartRows, fallbackSheet } from '#lib/server/data.js';

export function load() {
	return { explorer: true, format: 'jnj', rows: chartRows('jnj'), fallback: fallbackSheet('jnj') };
}
