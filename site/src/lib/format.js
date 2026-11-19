import { resolve } from '$app/paths';

/** A site path ("/strictly/") with the base path prepended. Call it while rendering. */
export const link = (/** @type {string} */ path) => resolve(/** @type {any} */ (path.slice(1)));

/** A metric value, to a fixed number of decimal places (4 by default). */
export const fx = (/** @type {number} */ v, digits = 4) => (Number.isFinite(v) ? v.toFixed(digits) : '—');

/** A value that may be a whole number (rank sums, counts): no decimals if it is one. */
export const nice = (/** @type {number} */ v, digits = 3) =>
	Number.isInteger(v) ? String(v) : v.toFixed(digits);

/** A signed value with a real minus sign. */
export const signed = (/** @type {number} */ v, digits = 3) =>
	(v < 0 ? '−' : v > 0 ? '+' : '') + nice(Math.abs(v), digits);

/** Negative numbers with a real minus sign. */
export const minus = (/** @type {string} */ s) => s.replace(/^-/, '−');

/** "2025-03-08" → "8 Mar 2025". */
export const date = (/** @type {string} */ iso) =>
	new Date(iso + 'T00:00:00Z').toLocaleDateString('en-NZ', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
