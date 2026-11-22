<script>
	// Every metric for one scoresheet: its value, recalculated here and checked against the
	// precomputed one, and its percentile among the finals of the same format.
	import Term from './Term.svelte';
	import PercentileTrack from './PercentileTrack.svelte';
	import { FAMILIES, METRICS } from '#lib/families.js';
	import { FORMATS } from '#lib/levels.js';
	import { allMetrics, TOLERANCE } from '#lib/metrics.js';
	import { explain, rank, unranked } from '#lib/percentiles.js';
	import { fx, minus } from '#lib/format.js';

	/**
	 * `onmetric`, where given, is called with a metric's key when its name is clicked; otherwise
	 * the name links to its family's section of the page. `current` is the metric to pick out.
	 * @type {{sheet: import('#lib/server/data.js').Sheet, percentiles: Record<string, import('#lib/percentiles.js').Percentile>,
	 *   current?: string, onmetric?: (key: string) => void}}
	 */
	let { sheet, percentiles, current, onmetric } = $props();
	const group = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (sheet.format)].label);
	const js = $derived(/** @type {Record<string, number>} */ (allMetrics(sheet.R)));
</script>

<div class="table-wrap">
	<table>
		<thead><tr><th>Metric</th><th></th><th class="num">Value</th><th></th><th class="num">Percentile</th><th></th></tr></thead>
		<tbody>
			{#each FAMILIES as f (f.id)}
				{#each f.metrics as k (k)}
					{@const p = percentiles[k]}
					<tr class:current={k === current}>
						<td>
							{#if onmetric}<button type="button" class="name" onclick={() => onmetric(k)}>{METRICS[k].label}</button>
							{:else}<a href="#{f.id}">{METRICS[k].label}</a>{/if}
						</td>
						<td class="muted small">{METRICS[k].higher ? 'higher' : 'lower'} = more agreement</td>
						<td class="num">{minus(fx(js[k], 6))}</td>
						{#if Math.abs(js[k] - sheet.py[k]) <= TOLERANCE}
							{@const tip = `Recalculated in your browser; matches the precomputed value used in the charts (${minus(fx(sheet.py[k], 6))})`}
							<td class="ok"><Term {tip} plain>✓</Term></td>
						{:else}
							<td class="bad">✗ precomputed: {minus(fx(sheet.py[k], 6))}</td>
						{/if}
						{#if p}
							<td class="num"><Term tip={explain(k, p, group)}>{rank(p)}</Term></td>
							<td><PercentileTrack pct={p.pct} /></td>
						{:else}
							<td class="num muted"><Term tip={unranked(k)} plain>–</Term></td>
							<td></td>
						{/if}
					</tr>
				{/each}
			{/each}
		</tbody>
	</table>
</div>

<style>
	.ok { color: var(--ok); }
	.bad { color: var(--bad); font-weight: 700; }
	.name { font: inherit; padding: 0; border: 0; background: none; color: var(--link); text-align: left; text-decoration: underline; cursor: pointer; }
	.current td { background: var(--surface-2); }
	.current .name { font-weight: 600; }
</style>
