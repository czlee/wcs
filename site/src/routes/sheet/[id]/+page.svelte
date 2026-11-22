<script>
	import SheetMeta from '#lib/components/SheetMeta.svelte';
	import RankMatrix from '#lib/components/RankMatrix.svelte';
	import MetricsTable from '#lib/components/MetricsTable.svelte';
	import WorkedSquared from '#lib/components/WorkedSquared.svelte';
	import WorkedHeadToHead from '#lib/components/WorkedHeadToHead.svelte';
	import WorkedTop from '#lib/components/WorkedTop.svelte';
	import WorkedGaps from '#lib/components/WorkedGaps.svelte';
	import { FAMILIES } from '#lib/families.js';
	import { FORMATS } from '#lib/levels.js';
	import { link } from '#lib/format.js';

	let { data } = $props();
	const s = $derived(data.sheet);
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (s.format)]);
	const group = $derived(fmt.label);

	const WORKED = { l2: WorkedSquared, l1: WorkedGaps, 'head-to-head': WorkedHeadToHead, top: WorkedTop };
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
	The percentile compares this final with the other {group} finals, at every level: 100th is the most agreement, whichever way the metric runs.
</p>
<MetricsTable sheet={s} percentiles={data.percentiles} />

{#each FAMILIES as f (f.id)}
	{@const Worked = WORKED[/** @type {keyof typeof WORKED} */ (f.id)]}
	<h2 id={f.id}>{f.title}</h2>
	<p class="small muted">What these metrics mean and how they compare across levels: <a href={link(`${fmt.longPath}#${f.id}`)}>{fmt.label} results, long-form</a>.</p>
	<Worked sheet={s} />
{/each}

<style>
	.crumb { font-size: 0.85rem; margin-top: 1em; }
	h1 { font-size: 1.4rem; }
	.ok { color: var(--ok); }
</style>
