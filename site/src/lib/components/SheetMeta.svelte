<script>
	import { FORMATS, LEVEL_LABEL } from '#lib/levels.js';
	import { date } from '#lib/format.js';
	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();
</script>

<dl class="meta">
	<dt>Event</dt><dd>{sheet.event}</dd>
	<dt>Division</dt><dd>{sheet.name}</dd>
	<dt>Date</dt><dd>{date(sheet.date)}</dd>
	<dt>Counted as</dt><dd>{FORMATS[/** @type {'jnj'|'strictly'} */ (sheet.format)].label}, {LEVEL_LABEL[sheet.level]}</dd>
	<dt>Size</dt><dd>{sheet.judges.length} judges × {sheet.competitors.length} competitors</dd>
	<dt>Source</dt><dd><a href={sheet.url} rel="external noopener">{sheet.site}</a> <span class="muted small">(the published scoresheet; compare the ranks below with it)</span></dd>
</dl>

<style>
	.meta { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0.1em 1em; margin: 0.6em 0; font-size: 0.9rem; }
	dt { color: var(--text-3); }
	dd { margin: 0; overflow-wrap: anywhere; }
</style>
