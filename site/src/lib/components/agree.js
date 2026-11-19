/** Cell background for an agreement value scaled to 0..1 (1 = full agreement). */
export const agreeBg = (/** @type {number} */ t) => {
	const c = Math.max(0, Math.min(1, t));
	return `color-mix(in srgb, var(--ok) ${Math.round(45 * c)}%, transparent)`;
};
/** Cell background for a disagreement value scaled to 0..1 (1 = maximal disagreement). */
export const disagreeBg = (/** @type {number} */ t) => {
	const c = Math.max(0, Math.min(1, t));
	return `color-mix(in srgb, var(--bad) ${Math.round(45 * c)}%, transparent)`;
};
