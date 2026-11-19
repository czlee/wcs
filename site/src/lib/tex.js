// Numbers for substituting into TeX formulas.

/** A number to `digits` decimal places, or as an integer if it is one. */
export const tn = (/** @type {number} */ v, digits = 4) => (Number.isInteger(v) ? String(v) : v.toFixed(digits));

/** As tn, but in parentheses if negative (for "1 − (−0.12)"). */
export const tp = (/** @type {number} */ v, digits = 4) => (v < 0 ? `(${tn(v, digits)})` : tn(v, digits));
