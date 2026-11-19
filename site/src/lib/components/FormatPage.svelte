<script>
	// The results page for one dance format (Jack & Jill or Strictly): intro,
	// limitations, how to read the page, then each family of metrics with its working on an
	// example scoresheet and its charts by level.
	import { onMount } from 'svelte';
	import Limitations from './Limitations.svelte';
	import MetricChart from './MetricChart.svelte';
	import WorkedConcordance from './WorkedConcordance.svelte';
	import WorkedOrder from './WorkedOrder.svelte';
	import WorkedTop from './WorkedTop.svelte';
	import WorkedSpread from './WorkedSpread.svelte';
	import Switch from './Switch.svelte';
	import { FAMILIES, METRICS, METRIC_KEYS } from '#lib/families.js';
	import { FORMATS } from '#lib/levels.js';
	import { link, date } from '#lib/format.js';

	let { data } = $props();
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (data.format)]);
	const other = $derived(Object.values(FORMATS).find((f) => f.id !== data.format));
	const rows = $derived(data.rows);
	const WORKED = { concordance: WorkedConcordance, order: WorkedOrder, top: WorkedTop, spread: WorkedSpread };
	const INTRO = {
		concordance: 'How much does the panel agree on one order? Kendall’s W looks at the panel as a whole; the mean pairwise Spearman ρ averages the agreement between each pair of judges.',
		order: 'How often do two judges put competitors in the same order? These compare each pair of judges, then average over all the pairs on the panel.',
		top: 'Do the judges agree on who belongs at the top, whatever the order?',
		spread: 'For each competitor, how far apart are the ranks the judges gave them?'
	};

	// Which option of each family's switch is chosen (an index into f.switch.options).
	/** @type {Record<string, number>} */
	let picked = $state(Object.fromEntries(FAMILIES.map((f) => [f.id, 0])));

	// The fallback until a random one loads (writable: pickRandom replaces it).
	let example = $derived(/** @type {import('#lib/server/data.js').Sheet} */ (data.fallback));
	let loading = $state(false);
	async function pickRandom() {
		const ids = rows.map((/** @type {any} */ r) => r.id).filter((/** @type {string} */ id) => id !== example.id);
		const id = ids[Math.floor(Math.random() * ids.length)];
		loading = true;
		try {
			const res = await fetch(link(`/sheet/${id}/data.json`));
			if (res.ok) { example = await res.json(); }
		} finally {
			loading = false;
		}
	}
	onMount(pickRandom);
</script>

<h1>How much do WCS judges disagree? <span class="fmt" style:--c={fmt.colour}>{fmt.label} finals</span></h1>
<p class="byline">By Chuan-Zheng Lee<span class="credit">, with implementation by Claude</span></p>
<p class="lede">
	In a West Coast Swing final, every judge ranks every competitor, and relative placement combines those
	rankings into the result. This page looks at the rankings before they’re combined: how different are
	the judges’ rankings from each other, and does that vary by division level? It covers
	<strong>{rows.length} {fmt.label} finals</strong> from {date(data.info.first_event)} to {date(data.info.last_event)}.
	{#if other}<a href={link(other.path)}>{other.label} finals are on their own page.</a>{/if}
</p>
<p class="lede">
	Every number here can be checked. Each scoresheet links to its published source, and this page
	recalculates every metric in your browser, step by step, and checks the result against the analysis.
</p>

<Limitations info={data.info} />

<h2 id="reading">Reading this page</h2>
<p>
	There are many ways to measure how far apart rankings are, and they don’t all answer the same question.
	This page uses twelve, in four families. For each family it explains the metrics, works them through on
	one scoresheet, and then shows the results for every level. Some metrics are close variants of each other,
	so they share a chart, and a switch above the charts picks which one it shows.
</p>

{#each FAMILIES as f (f.id)}
	{@const Worked = WORKED[/** @type {keyof typeof WORKED} */ (f.id)]}
	<section class="family">
		<h2 id={f.id}>{f.title}</h2>
		<p class="intro">{INTRO[/** @type {keyof typeof INTRO} */ (f.id)]}</p>
		<details class="worked">
			<summary>How is this calculated?</summary>
			<p class="example">
				Example scoresheet chosen at random: <strong>{example.name}</strong> ({date(example.date)}).
				<button class="btn" onclick={pickRandom} disabled={loading}>{loading ? 'Loading…' : 'Pick another'}</button> ·
				<a href={link(`/sheet/${example.id}/`)}>More details</a> ·
				<a href={link(`/sheets/?format=${data.format}`)}>All scoresheets</a>
			</p>
			{#key example.id}<Worked sheet={example} />{/key}
		</details>
		{#if f.switch}
			<p class="switch-row">
				Show:
				<Switch label={f.switch.label} options={f.switch.options.map((label, i) => ({ value: i, label }))} bind:value={picked[f.id]} />
			</p>
		{/if}
		{#each f.charts as variants, ci (ci)}
			{@const k = variants[Math.min(picked[f.id], variants.length - 1)]}
			{@const meta = METRICS[k]}
			<h3 class="metric">{meta.label}</h3>
			<MetricChart {rows} index={METRIC_KEYS.indexOf(k)} {meta} colour={fmt.colour} format={data.format} />
		{/each}
	</section>
{/each}

<style>
	.fmt { color: color-mix(in srgb, var(--c) 80%, var(--text)); white-space: nowrap; }
	.byline { margin-top: -0.4em; color: var(--text-2); font-size: 0.9rem; }
	.byline .credit { color: var(--text-3); }
	.lede { font-size: 1.05rem; }
	.intro { font-size: 1.02rem; }
	.worked {
		border: 1px solid var(--border); border-radius: 6px; padding: 0.4em 0.9em 0.6em; margin: 0.8em 0 1.4em;
	}
	.worked summary { cursor: pointer; font-weight: 600; color: var(--text-2); }
	.worked[open] summary { margin-bottom: 0.4em; }
	h3.metric { margin-top: 1.8em; }
	.switch-row { margin: 1.2em 0 -0.6em; color: var(--text-2); font-size: 0.9rem; }
	.example { font-size: 0.92rem; color: var(--text-2); }
	.btn { margin: 0 0.1em; }
</style>
