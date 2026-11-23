import { chartRows, fallbackSheet, profile } from '#lib/server/data.js';

export function load() {
	return { format: 'strictly', rows: chartRows('strictly'), fallback: profile(fallbackSheet('strictly')) };
}
