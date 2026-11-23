/** Division levels, lowest to highest, as exported by scripts/export_site_data.py. */
export const LEVELS = [
	{ id: 'new', label: 'Newcomer', short: 'New' },
	{ id: 'nov', label: 'Novice', short: 'Nov' },
	{ id: 'int', label: 'Intermediate', short: 'Int' },
	{ id: 'adv', label: 'Advanced', short: 'Adv' },
	{ id: 'als', label: 'All-Star', short: 'AlS' },
	{ id: 'chp', label: 'Champions', short: 'Chp' }
];
export const LEVEL_LABEL = Object.fromEntries(LEVELS.map((l) => [l.id, l.label]));

/**
 * Dance formats: each has its own pages and colour, and the two never share a chart.
 * `path` is its explorer's.
 */
export const FORMATS = {
	jnj: { id: 'jnj', label: 'Jack & Jill', path: '/', colour: 'var(--jnj)' },
	strictly: { id: 'strictly', label: 'Strictly', path: '/strictly/', colour: 'var(--strictly)' }
};
