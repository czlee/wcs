import { chartRows, fallbackSheet } from '#lib/server/data.js';

export function load() {
	return { format: 'jnj', rows: chartRows('jnj'), fallback: fallbackSheet('jnj') };
}
