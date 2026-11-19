<script>
	import SheetMeta from '#lib/components/SheetMeta.svelte';
	import RankMatrix from '#lib/components/RankMatrix.svelte';
	import WorkedConcordance from '#lib/components/WorkedConcordance.svelte';
	import WorkedOrder from '#lib/components/WorkedOrder.svelte';
	import WorkedTop from '#lib/components/WorkedTop.svelte';
	import WorkedSpread from '#lib/components/WorkedSpread.svelte';
	import { FAMILIES, METRICS } from '#lib/families.js';
	import { FORMATS } from '#lib/levels.js';
	import { allMetrics, TOLERANCE } from '#lib/metrics.js';
	import { link, fx, minus } from '#lib/format.js';

	let { data } = $props();
	const s = $derived(data.sheet);
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (s.format)]);
	const js = $derived(/** @type {Record<string, number>} */ (allMetrics(s.R)));
	const WORKED = { concordance: WorkedConcordance, order: WorkedOrder, top: WorkedTop, spread: WorkedSpread };
</script>

<svelte:head>
	<title>{s.name} · WCS judge divergence</title>
	<meta name="description" content="Every divergence metric for {s.name}, worked through from the judges’ rankings." />
</svelte:head>

<p class="crumb"><a href={link(fmt.path)}>← {fmt.label} results</a> · <a href={link(`/sheets/?format=${s.format}&level=${s.level}`)}>other scoresheets at this level</a></p>
<h1>{s.name}</h1>
<SheetMeta sheet={s} />
<RankMatrix sheet={s} caption="Each judge’s ranks (1 = first), competitors in the order on the scoresheet" />

<h2>All twelve metrics</h2>
<p>
	Recalculated in your browser from the ranks above, and checked against the analysis
	(<code>compute_metrics.py</code>), whose values are the ones in the charts. The working for each is below.
</p>
<div class="table-wrap">
	<table>
		<thead><tr><th>Metric</th><th></th><th class="num">This page</th><th class="num">Analysis</th><th></th></tr></thead>
		<tbody>
			{#each FAMILIES as f (f.id)}
				{#each f.metrics as k (k)}
					{@const ok = Math.abs(js[k] - s.py[k]) <= TOLERANCE}
					<tr>
						<td><a href="#{f.id}">{METRICS[k].label}</a></td>
						<td class="muted small">{METRICS[k].higher ? 'higher' : 'lower'} = more agreement</td>
						<td class="num">{minus(fx(js[k], 6))}</td>
						<td class="num">{minus(fx(s.py[k], 6))}</td>
						<td class:ok class:bad={!ok}>{ok ? '✓' : '✗'}</td>
					</tr>
				{/each}
			{/each}
		</tbody>
	</table>
</div>

{#each FAMILIES as f (f.id)}
	{@const Worked = WORKED[/** @type {keyof typeof WORKED} */ (f.id)]}
	<h2 id={f.id}>{f.title}</h2>
	<p class="small muted">What these metrics mean and how they compare across levels: <a href={link(`${fmt.path}#${f.id}`)}>{fmt.label} results</a>.</p>
	<Worked sheet={s} />
{/each}

<style>
	.crumb { font-size: 0.85rem; margin-top: 1em; }
	h1 { font-size: 1.4rem; }
	.ok { color: var(--ok); }
	.bad { color: var(--bad); font-weight: 700; }
</style>
