<script>
	// One metric's value for one scoresheet, and where that falls among the finals of its format.
	import PercentileTrack from './PercentileTrack.svelte';
	import { METRICS } from '#lib/families.js';
	import { FORMATS } from '#lib/levels.js';
	import { explain, rank, unranked } from '#lib/percentiles.js';
	import { fx, minus } from '#lib/format.js';

	/** @type {{sheet: import('#lib/server/data.js').Profile, metric: string}} */
	let { sheet, metric } = $props();
	const p = $derived(sheet.percentiles[metric]);
	const group = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (sheet.format)].label);
</script>

<div class="standing">
	<div class="fig">
		<span class="label">Value</span>
		<strong>{minus(fx(sheet.py[metric]))}</strong>
		<span class="note">{METRICS[metric].higher ? 'Higher' : 'Lower'} means more agreement</span>
	</div>
	<div class="fig">
		<span class="label">Percentile</span>
		{#if p}
			<strong>{rank(p)} <span class="track"><PercentileTrack pct={p.pct} /></span></strong>
			<span class="note">{explain(metric, p, group)}</span>
		{:else}
			<strong>–</strong>
			<span class="note">{unranked(metric)}</span>
		{/if}
	</div>
</div>

<style>
	.standing {
		display: flex; flex-wrap: wrap; gap: 0.5em 2.5em; margin: 0.7em 0; padding: 0.5em 0.9em;
		border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2);
	}
	.fig { display: flex; flex-direction: column; }
	.label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-3); }
	strong { font-size: 1.1rem; font-variant-numeric: tabular-nums; }
	.track { margin-left: 0.3em; } /* the track's mark overhangs its left end at 0 */
	.note { font-size: 0.82rem; color: var(--text-2); }
</style>
