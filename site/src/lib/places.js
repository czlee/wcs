// Names for the country and US state codes in the exported data (from lookups/regions.json).
const US_STATES = /** @type {Record<string, string>} */ ({
	AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut',
	DE: 'Delaware', DC: 'Washington, DC', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois',
	IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
	MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana',
	NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
	NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania',
	RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah',
	VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming'
});
const SHORT = /** @type {Record<string, string>} */ ({ US: 'USA', GB: 'UK' });
const names = new Intl.DisplayNames(['en'], { type: 'region' });

/** "California, USA" for US-CA, "Germany" for DE, and nothing if the country isn't known. */
export function place(/** @type {string | null} */ country, /** @type {string | null} */ state) {
	if (!country) return '';
	const c = SHORT[country] ?? names.of(country) ?? country;
	const s = state && US_STATES[state.replace(/^US-/, '')];
	return s ? `${s}, ${c}` : c;
}
