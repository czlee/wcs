<script>
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Tex from './Tex.svelte';
	import { topN, judgePairs } from '#lib/metrics.js';
	import { fx } from '#lib/format.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const pairs = $derived(judgePairs(m));
	let N = $state(3);
	/** @type {[number, number]} */
	let selected = $state([0, 1]);
	$effect(() => { if (selected[1] >= m) selected = [0, 1]; });
	const t = (/** @type {number} */ a, /** @type {number} */ b) => topN(sheet.R[a], sheet.R[b], N);
	const mean = (/** @type {'overlap'|'jaccard'} */ k) => pairs.reduce((s, [a, b]) => s + t(a, b)[k], 0) / pairs.length;
	const overlap = $derived(mean('overlap'));
	const jaccard = $derived(mean('jaccard'));
	// Competitors in a judge's top N, best first.
	const top = (/** @type {number} */ j) =>
		sheet.R[j].flatMap((r, i) => (r <= N ? [i] : [])).toSorted((x, y) => sheet.R[j][x] - sheet.R[j][y]);
</script>

<p>
	These ignore the order within the top places and ask only <em>who</em> made them. For a pair of judges,
	take the sets <Tex tex="A" /> and <Tex tex="B" /> of competitors each ranked 1st to <Tex tex="N" />th, and
	count how many are in both.
</p>
<Tex display tex={String.raw`\text{overlap} = \frac{|A \cap B|}{N} \qquad \text{Jaccard} = \frac{|A \cap B|}{|A \cup B|}`} />
<p>
	Both sets have <Tex tex="N" /> members, so with <Tex tex="k" /> in common,
	<Tex tex={String.raw`\text{Jaccard} = \frac{k}{2N - k}`} />: for a single pair it carries the same
	information as overlap on a different scale. Averaged over pairs, the two differ slightly.
</p>
<div class="toggle" role="group" aria-label="Top N">
	{#each [3, 5] as k (k)}<button aria-pressed={N === k} onclick={() => (N = k)}>Top {k}</button>{/each}
</div>
<PairMatrix
	judges={sheet.judges}
	value={(a, b) => t(a, b).inter.length}
	fmt={(v) => String(v)}
	colour={(v) => agreeBg(v / N)}
	bind:selected
	label="Number of competitors in both judges’ top {N}"
>
	{#snippet detail(a, b)}
		{@const x = t(a, b)}
		<h4>J{a + 1} {sheet.judges[a]} and J{b + 1} {sheet.judges[b]}</h4>
		<div class="sets">
			{#each [a, b] as j (j)}
				<div>
					<strong>J{j + 1}’s top {N}</strong>
					<ol>
						{#each top(j) as i (i)}<li class:both={x.inter.includes(i)}>{sheet.competitors[i]}</li>{/each}
					</ol>
				</div>
			{/each}
		</div>
		<p class="small">Highlighted: in both ({x.inter.length}). In either: {x.union.length}.</p>
		<Tex display tex={String.raw`\text{overlap} = \frac{${x.inter.length}}{${N}} = ${fx(x.overlap)} \qquad \text{Jaccard} = \frac{${x.inter.length}}{${x.union.length}} = ${fx(x.jaccard)}`} />
	{/snippet}
</PairMatrix>
<p class="small muted">Cells show how many competitors are in both judges’ top {N}, out of {N}.</p>
<Check label="Mean overlap @ {N}" js={overlap} py={sheet.py[`overlap_at_${N}`]} />
<Check label="Mean Jaccard @ {N}" js={jaccard} py={sheet.py[`jaccard_at_${N}`]} />
{#if n < 2 * N}
	<p class="callout small">
		With only {n} competitors, any two top-{N} sets must share at least
		<Tex tex={String.raw`2N - n = 2 \times ${N} - ${n} = ${2 * N - n}`} />
		{2 * N - n === 1 ? 'competitor' : 'competitors'}{#if n === N}: here every judge’s top {N} is the whole field, so both values are exactly 1{/if}.
		Small finals push these metrics up regardless of how much the judges agree.
	</p>
{/if}

<style>
	.toggle { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; margin: 0.4em 0; }
	.toggle button { font: inherit; font-size: 0.85rem; padding: 0.25em 0.9em; border: 0; background: transparent; color: var(--text-2); cursor: pointer; }
	.toggle button[aria-pressed='true'] { background: var(--text); color: var(--surface); }
	.sets { display: flex; flex-wrap: wrap; gap: 0.5em 1.5em; }
	.sets ol { margin: 0.2em 0; padding-left: 1.4em; }
	.both { background: var(--highlight-bg); }
</style>
