<script>
	import Term from '#lib/components/Term.svelte';
	import SheetMeta from '#lib/components/SheetMeta.svelte';
	import RankMatrix from '#lib/components/RankMatrix.svelte';
	import WorkedConcordance from '#lib/components/WorkedConcordance.svelte';
	import WorkedOrder from '#lib/components/WorkedOrder.svelte';
	import WorkedTop from '#lib/components/WorkedTop.svelte';
	import WorkedSpread from '#lib/components/WorkedSpread.svelte';
	import { FAMILIES, METRICS } from '#lib/families.js';
	import { FORMATS, LEVEL_LABEL } from '#lib/levels.js';
	import { allMetrics, TOLERANCE } from '#lib/metrics.js';
	import { link, fx, minus } from '#lib/format.js';

	let { data } = $props();
	const s = $derived(data.sheet);
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (s.format)]);
	const js = $derived(/** @type {Record<string, number>} */ (allMetrics(s.R)));
	const pct = $derived(data.percentiles);
	const group = $derived(`${LEVEL_LABEL[s.level]} ${fmt.label}`);

	/** 40 → "40th", 1 → "1st", 12 → "12th". */
	function ordinal(/** @type {number} */ n) {
		const t = n % 100, u = n % 10;
		return n + (t >= 11 && t <= 13 ? 'th' : u === 1 ? 'st' : u === 2 ? 'nd' : u === 3 ? 'rd' : 'th');
	}

	/** The tooltip for a percentile: how many finals it compares against, and how. */
	function pctTip(/** @type {string} */ k) {
		const p = pct[k];
		const minN = METRICS[k].minN;
		return `More agreement than ${Math.round(p.pct)}% of the ${p.of} ${group} finals` +
			(minN ? ` with at least ${minN} competitors` : '') +
			` on this metric (100th = the most agreement).`;
	}
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
	Recalculated in your browser from the ranks above, as an independent check on the analysis code.
	A <span class="ok">✓</span> means the result matches the precomputed value used in the charts. The working for each is below.
	The percentile compares this final with the other {group} finals: 100th is the most agreement, whichever way the metric runs.
</p>
<div class="table-wrap">
	<table>
		<thead><tr><th>Metric</th><th></th><th class="num">Value</th><th></th><th class="num">Percentile</th></tr></thead>
		<tbody>
			{#each FAMILIES as f (f.id)}
				{#each f.metrics as k (k)}
					{@const ok = Math.abs(js[k] - s.py[k]) <= TOLERANCE}
					<tr>
						<td><a href="#{f.id}">{METRICS[k].label}</a></td>
						<td class="muted small">{METRICS[k].higher ? 'higher' : 'lower'} = more agreement</td>
						<td class="num">{minus(fx(js[k], 6))}</td>
						{#if ok}
							{@const tip = `Recalculated in your browser; matches the precomputed value used in the charts (${minus(fx(s.py[k], 6))})`}
							<td class="ok"><Term {tip} plain>✓</Term></td>
						{:else}
							<td class="bad">✗ precomputed: {minus(fx(s.py[k], 6))}</td>
						{/if}
						{#if pct[k]}
							<td class="num"><Term tip={pctTip(k)}>{ordinal(Math.round(pct[k].pct))}</Term></td>
						{:else}
							{@const tip = `Not ranked: finals with fewer than ${METRICS[k].minN} competitors are left out of this metric’s charts`}
							<td class="num muted"><Term {tip} plain>–</Term></td>
						{/if}
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
