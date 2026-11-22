import { chartRows, fallbackSheet, profile } from '#lib/server/data.js';

export function load() {
	return { explorer: true, format: 'jnj', rows: chartRows('jnj'), fallback: profile(fallbackSheet('jnj')) };
}
