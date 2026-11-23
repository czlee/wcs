/**
 * Coarse regions, as the ISO 3166-1 alpha-2 country codes in each. These are only as fine as
 * the data allows: Canada and Asia have too few finals to stand alone. Every exported country
 * must be in one (server/data.js checks), or its scoresheets would vanish from filtered views.
 *
 * Region ids are URL values (see dimensions.js), so keep them stable.
 * @type {{id: string, label: string, countries: Set<string>}[]}
 */
export const REGIONS = [
	{ id: 'north-america', label: 'North America', countries: codes('US CA MX') },
	{
		// Russia is here because its events have been in European Russia.
		id: 'europe', label: 'Europe',
		countries: codes(`AL AD AT BA BE BG BY CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LI LT LU LV
			MC MD ME MK MT NL NO PL PT RO RS RU SE SI SK SM UA XK`)
	},
	{ id: 'asia-pacific', label: 'Asia–Pacific', countries: codes('AU NZ CN HK ID IN JP KR MY PH SG TH TW VN') }
];

function codes(/** @type {string} */ list) {
	return new Set(list.split(/\s+/));
}

/** The id of a country's region, if it has one. */
export const regionOf = (/** @type {string | null} */ country) =>
	REGIONS.find((r) => country && r.countries.has(country))?.id;
