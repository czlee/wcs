import { chartRows, fallbackSheet, profile } from '#lib/server/data.js';

export function load() {
	return { format: 'jnj', rows: chartRows('jnj'), fallback: profile(fallbackSheet('jnj')) };
}
