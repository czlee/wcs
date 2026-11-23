<script>
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import MetricLink from './MetricLink.svelte';
	import Tex from './Tex.svelte';
	import { topN, topNChance, chanceCorrected, judgePairs } from '#lib/metrics.js';
	import { METRICS } from '#lib/families.js';
	import { fx, minus } from '#lib/format.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	// Alongside the working of `focus` (a metric key), the other metrics' is still shown
	// (overlap and Jaccard explain each other), but dimmed, and a note says which is which.
	const ov = $derived(focus.startsWith('overlap'));
	const jc = $derived(focus.startsWith('jaccard'));
	const cc = $derived(focus.endsWith('_cc'));
	// Inside the chance-correction section, which is dimmed as a whole when it isn't in focus,
	// only dim the other metric when the section itself is in focus (so nothing is dimmed twice).
	const dimO = $derived(!ov && cc), dimJ = $derived(!jc && cc);
	const N = 3;
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const pairs = $derived(judgePairs(m));
	/** @type {[number, number]} */
	let selected = $state([0, 1]);
	$effect(() => { if (selected[1] >= m) selected = [0, 1]; });
	const t = (/** @type {number} */ a, /** @type {number} */ b) => topN(sheet.R[a], sheet.R[b], N);
	const mean = (/** @type {'overlap'|'jaccard'} */ k) => pairs.reduce((s, [a, b]) => s + t(a, b)[k], 0) / pairs.length;
	const overlap = $derived(mean('overlap'));
	const jaccard = $derived(mean('jaccard'));
	const chance = $derived(topNChance(n, N));
	const overlapCC = $derived(chanceCorrected(overlap, chance.overlap));
	const jaccardCC = $derived(chanceCorrected(jaccard, chance.jaccard));
	const minN = /** @type {number} */ (METRICS.overlap_at_3_cc.minN);
	// Competitors in a judge's top N, best first.
	const top = (/** @type {number} */ j) =>
		sheet.R[j].flatMap((r, i) => (r <= N ? [i] : [])).toSorted((x, y) => sheet.R[j][x] - sheet.R[j][y]);
	const tx = (/** @type {number} */ v) => minus(fx(v));
</script>

<p>
	This metric ignores the order within the top {N} places and asks only
	<em>who</em> made them. For a pair of judges, take the sets <Tex tex="A" /> and <Tex tex="B" /> of competitors each
	ranked 1st to {N}rd, and count how many are in both. There are two ways to turn that into a score: the overlap
	divides it by {N}, and the Jaccard index divides it by how many are in either set.
</p>
<p class="small muted">
	The metric you’re looking at is the {ov ? 'overlap' : 'Jaccard index'}{cc ? ', corrected for chance (the last step)' : ', without a correction for chance'}.
	The {#if ov}<MetricLink k={cc ? 'jaccard_at_3_cc' : 'jaccard_at_3'}>Jaccard index</MetricLink>{:else}<MetricLink k={cc ? 'overlap_at_3_cc' : 'overlap_at_3'}>overlap</MetricLink>{/if} {cc ? 'is' : 'and the chance correction are'} dimmed, for comparison.
</p>
{#snippet pair(/** @type {string} */ o, /** @type {string} */ j, inner = false)}
	<div class="eqs">
		<div class:dim={inner ? dimO : !ov}><Tex display tex={o} /></div>
		<div class:dim={inner ? dimJ : !jc}><Tex display tex={j} /></div>
	</div>
{/snippet}
{@render pair(String.raw`\text{overlap} = \frac{|A \cap B|}{${N}}`, String.raw`\text{Jaccard} = \frac{|A \cap B|}{|A \cup B|}`)}
<p>
	Both sets have {N} members, so with <Tex tex="k" /> in common,
	<Tex tex={String.raw`\text{Jaccard} = \frac{k}{${2 * N} - k}`} />: for a single pair it carries the same
	information as overlap on a different scale. Averaged over pairs, the two differ slightly.
</p>
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
		{@render pair(String.raw`\text{overlap} = \frac{${x.inter.length}}{${N}} = ${fx(x.overlap)}`, String.raw`\text{Jaccard} = \frac{${x.inter.length}}{${x.union.length}} = ${fx(x.jaccard)}`)}
	{/snippet}
</PairMatrix>
<p class="small muted">Cells show how many competitors are in both judges’ top {N}, out of {N}.</p>
<p>Averaging over all {pairs.length} pairs of judges:</p>
<div class:dim={!ov}><Check label="Mean overlap @ {N}" js={overlap} py={sheet.py.overlap_at_3} /></div>
<div class:dim={!jc}><Check label="Mean Jaccard @ {N}" js={jaccard} py={sheet.py.jaccard_at_3} /></div>

<div class:dim={!cc}>
<h4>Correcting for chance</h4>
<p>
	Two judges picking their top {N} at random would still share some competitors, and more often in a small
	final. If each judge’s top {N} were a random {N} of the <Tex tex={`n = ${n}`} /> competitors, the number in both,
	<Tex tex="i" />, would follow a hypergeometric distribution, with expected values
</p>
<div class:dim={dimO}><Tex display tex={String.raw`\mathbb{E}[\text{overlap}] = \frac{${N}}{n} = \frac{${N}}{${n}} = ${fx(chance.overlap)}`} /></div>
<div class:dim={dimJ}><Tex display tex={String.raw`\mathbb{E}[\text{Jaccard}] = \sum_i \frac{\binom{${N}}{i}\binom{n-${N}}{${N}-i}}{\binom{n}{${N}}} \cdot \frac{i}{${2 * N} - i} = ${chance.terms.map((c) => `${fx(c.p)} \\cdot ${fx(c.jaccard)}`).join(' + ')} = ${fx(chance.jaccard)}`} /></div>
<p>The corrected value rescales the mean over judge pairs, <Tex tex="x" />, so that 0 is chance-level agreement and 1 is identical top {N}s:</p>
<Tex display tex={String.raw`\text{corrected} = \frac{x - \mathbb{E}[x]}{1 - \mathbb{E}[x]}`} />
{@render pair(String.raw`\text{overlap} = \frac{${tx(overlap)} - ${fx(chance.overlap)}}{1 - ${fx(chance.overlap)}} = ${tx(overlapCC)}`, String.raw`\text{Jaccard} = \frac{${tx(jaccard)} - ${fx(chance.jaccard)}}{1 - ${fx(chance.jaccard)}} = ${tx(jaccardCC)}`, true)}
<div class:dim={dimO}><Check label="Mean overlap @ {N}, chance-corrected" js={overlapCC} py={sheet.py.overlap_at_3_cc} /></div>
<div class:dim={dimJ}><Check label="Mean Jaccard @ {N}, chance-corrected" js={jaccardCC} py={sheet.py.jaccard_at_3_cc} /></div>
<p class="small muted">
	This is a naive, first-pass correction. Real judges’ top {N}s aren’t random: they’re drawn towards the
	same strong competitors, more so in some fields than others. So it removes the chance level but not every
	way field size affects the result.
</p>
</div>
{#if n < minN}
	<p class="callout small">
		With only {n} competitors, any two top-{N} sets must share at least
		<Tex tex={String.raw`2 \times ${N} - ${n} = ${2 * N - n}`} />
		{2 * N - n === 1 ? 'competitor' : 'competitors'}, so this metric can’t reach its
		full range. Finals of fewer than {minN} are left out of the charts for this metric.
	</p>
{/if}

<style>
	.sets { display: flex; flex-wrap: wrap; gap: 0.5em 1.5em; }
	.sets ol { margin: 0.2em 0; padding-left: 1.4em; }
	.both { background: var(--highlight-bg); }
</style>
