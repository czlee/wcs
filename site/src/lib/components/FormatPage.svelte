<script>
	// The results page for one dance format (Jack & Jill or Strictly): intro,
	// limitations, the data, then each family of metrics with its working on an
	// example scoresheet and its charts by level.
	import { onMount } from 'svelte';
	import Limitations from './Limitations.svelte';
	import SheetMeta from './SheetMeta.svelte';
	import RankMatrix from './RankMatrix.svelte';
	import MetricChart from './MetricChart.svelte';
	import WorkedConcordance from './WorkedConcordance.svelte';
	import WorkedOrder from './WorkedOrder.svelte';
	import WorkedTop from './WorkedTop.svelte';
	import WorkedSpread from './WorkedSpread.svelte';
	import { FAMILIES, METRICS, METRIC_KEYS } from '#lib/families.js';
	import { FORMATS, LEVELS } from '#lib/levels.js';
	import { link, date } from '#lib/format.js';

	let { data } = $props();
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (data.format)]);
	const other = $derived(Object.values(FORMATS).find((f) => f.id !== data.format));
	const rows = $derived(data.rows);
	const WORKED = { concordance: WorkedConcordance, order: WorkedOrder, top: WorkedTop, spread: WorkedSpread };
	const INTRO = {
		concordance: 'How much does the panel, as a whole, agree on one order? Two numbers that carry the same information for any one scoresheet, but treat panel size differently.',
		order: 'How often do two judges put competitors in the same order? These compare each pair of judges, then average over all the pairs on the panel.',
		top: 'Do the judges agree on who belongs at the top, whatever the order?',
		spread: 'For each competitor, how far apart are the ranks the judges gave them?'
	};

	// The fallback until a random one loads (writable: pickRandom replaces it).
	let example = $derived(/** @type {import('#lib/server/data.js').Sheet} */ (data.fallback));
	let random = $state(false);
	let loading = $state(false);
	async function pickRandom() {
		const ids = rows.map((/** @type {any} */ r) => r.id).filter((/** @type {string} */ id) => id !== example.id);
		const id = ids[Math.floor(Math.random() * ids.length)];
		loading = true;
		try {
			const res = await fetch(link(`/sheet/${id}/data.json`));
			if (res.ok) { example = await res.json(); random = true; }
		} finally {
			loading = false;
		}
	}
	onMount(pickRandom);

	const levelStats = $derived(LEVELS.map((l) => {
		const rs = rows.filter((/** @type {any} */ r) => r.level === l.id);
		const avg = (/** @type {string} */ k) => rs.reduce((t, /** @type {any} */ r) => t + r[k], 0) / rs.length;
		return { level: l, count: rs.length, m: avg('m'), n: avg('n') };
	}));
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

<h2 id="data">The data</h2>
<p>
	Each scoresheet is one final: a ranking of the finalists by each judge. Panel and field sizes vary by
	level, which matters for several of the metrics below:
</p>
<div class="table-wrap">
	<table>
		<thead><tr><th>Level</th><th class="num">Scoresheets</th><th class="num">Mean judges</th><th class="num">Mean competitors</th></tr></thead>
		<tbody>
			{#each levelStats as s (s.level.id)}
				<tr>
					<td><a href={link(`/sheets/?format=${data.format}&level=${s.level.id}`)}>{s.level.label}</a></td>
					<td class="num">{s.count}</td>
					<td class="num">{s.count ? s.m.toFixed(1) : '—'}</td>
					<td class="num">{s.count ? s.n.toFixed(1) : '—'}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
<p>
	There are many ways to measure how far apart rankings are, and they don’t all answer the same question.
	This page uses twelve, in four families. For each family it explains the metrics, works them through on
	one scoresheet, and then shows the results for every level.
</p>

<h3 id="example">The example scoresheet</h3>
<p>
	{#if random}This one was picked at random from the {rows.length} on this page.{:else}This is the default example; your browser will swap in one picked at random.{/if}
	<button class="btn" onclick={pickRandom} disabled={loading}>{loading ? 'Loading…' : 'Pick another at random'}</button>
	<a href={link(`/sheet/${example.id}/`)}>Open it on its own page</a> ·
	<a href={link(`/sheets/?format=${data.format}`)}>choose any scoresheet</a>, or click any point in the charts.
</p>
<SheetMeta sheet={example} />
<RankMatrix sheet={example} caption="Each judge’s ranks (1 = first), competitors in the order on the scoresheet" />

<h3 id="charts">How to read the charts</h3>
<p>
	Each metric gets two charts, with one bar or box per level from Newcomer to Champions. On the
	<strong>left</strong> is the mean across that level’s scoresheets, with an interval of 1.96 standard errors
	either side (a provisional approximation of a 95% confidence interval; see the limitations). On the
	<strong>right</strong>, each dot is one scoresheet. The box spans the middle half (quartiles by linear
	interpolation), the line is the median, and the whiskers reach the furthest scoresheets within 1.5 box-lengths.
	Hover over anything for details. Click a dot for that scoresheet’s working, or a bar to list its scoresheets.
</p>

{#each FAMILIES as f (f.id)}
	{@const Worked = WORKED[/** @type {keyof typeof WORKED} */ (f.id)]}
	<section class="family">
		<h2 id={f.id}>{f.title}</h2>
		<p class="intro">{INTRO[/** @type {keyof typeof INTRO} */ (f.id)]}</p>
		<details class="worked" open>
			<summary>How it’s calculated, using the example scoresheet</summary>
			{#key example.id}<Worked sheet={example} />{/key}
		</details>
		{#each f.metrics as k (k)}
			{@const meta = METRICS[k]}
			<h3 class="metric">{meta.label} <span class="dir">{meta.higher ? 'higher' : 'lower'} = more agreement</span></h3>
			<MetricChart {rows} index={METRIC_KEYS.indexOf(k)} {meta} colour={fmt.colour} format={data.format} exampleId={example.id} />
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
	.dir { font-size: 0.8rem; font-weight: 400; color: var(--text-3); margin-left: 0.4em; }
	.btn { margin: 0 0.4em; }
</style>
