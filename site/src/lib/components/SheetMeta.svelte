<script>
	import { FORMATS, LEVEL_LABEL } from '#lib/levels.js';
	import { date } from '#lib/format.js';
	import { place } from '#lib/places.js';
	import icon from '#lib/assets/who-woulda-won.svg';
	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();

	// whowouldawon.dance takes the scoresheet's URL, and for eepro (one page, many divisions) the division too
	const wwwUrl = $derived.by(() => {
		const q = new URLSearchParams({ url: sheet.url });
		if (sheet.division) q.set('division', sheet.division);
		return `https://www.whowouldawon.dance/?${q}`;
	});
</script>

<dl class="meta">
	<dt>Event</dt><dd>{sheet.event}</dd>
	<dt>Competition</dt><dd>{sheet.name}</dd>
	<dt>Date</dt><dd>{date(sheet.date)}</dd>
	{#if place(sheet.country, sheet.state)}<dt>Location</dt><dd>{place(sheet.country, sheet.state)}</dd>{/if}
	<dt>Counted as</dt><dd>{FORMATS[/** @type {'jnj'|'strictly'} */ (sheet.format)].label}, {LEVEL_LABEL[sheet.level]}</dd>
	<dt>Size</dt><dd>{sheet.judges.length} judges × {sheet.competitors.length} competitors</dd>
	<dt>Source</dt><dd><a href={sheet.url} target="_blank" rel="external noopener">{sheet.url.replace(/^https?:\/\//, '')}</a></dd>
</dl>
<p class="www">
	<img src={icon} alt="" width="18" height="18" />
	<a href={wwwUrl} target="_blank" rel="external noopener">See who wins under different voting systems on <span class="name">Who Woulda Won</span></a>
</p>

<style>
	.meta { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0.1em 1em; margin: 0.6em 0; font-size: 0.9rem; }
	dt { color: var(--text-3); }
	dd { margin: 0; overflow-wrap: anywhere; }
	.www { display: flex; align-items: center; gap: 0.6em; margin: 0.8em 0; padding: 0.6em 0.8em; font-size: 0.9rem; background: var(--surface); border: 1px solid var(--border); border-radius: 6px; }
	.www .name { font-weight: 600; }
	.www img { flex: none; }
</style>
