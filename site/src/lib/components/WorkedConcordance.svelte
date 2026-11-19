<script>
	import RankMatrix from './RankMatrix.svelte';
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Term from './Term.svelte';
	import Tex from './Tex.svelte';
	import { kendallW, spearman, judgePairs } from '#lib/metrics.js';
	import { fx, nice, signed, minus } from '#lib/format.js';
	import { tn } from '#lib/tex.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();
	const w = $derived(kendallW(sheet.R));
	const m = $derived(w.m), n = $derived(w.n);
	const rhoBar = $derived((m * w.W - 1) / (m - 1));
	const rho = (/** @type {number} */ a, /** @type {number} */ b) => spearman(sheet.R[a], sheet.R[b]).rho;
	const pairs = $derived(judgePairs(m));
	const pairSum = $derived(pairs.reduce((t, [a, b]) => t + rho(a, b), 0));
	const pairMean = $derived(pairSum / pairs.length);
	/** @type {[number, number]} */
	let selected = $state([0, 1]);
	$effect(() => { if (selected[1] >= m) selected = [0, 1]; });
	const sp = $derived(spearman(sheet.R[selected[0]], sheet.R[selected[1]]));
</script>

<h4>Kendall’s W, step by step</h4>
<p>
	Add up the ranks each competitor got from the {m} judges. If the judges agreed completely, these
	rank sums would be as far apart as they can get: one competitor would get {m} firsts (a sum of {m}),
	the next {m} seconds (a sum of {2 * m}), and so on. If the judges’ rankings had nothing in common, every
	competitor’s sum would tend towards the same middle value,
	<Tex tex={String.raw`\tfrac{m(n+1)}{2} = \tfrac{${m} \times ${n + 1}}{2} = \mathbf{${tn(w.rBar, 1)}}`} />.
</p>
<RankMatrix
	{sheet}
	extras={[
		{ label: 'Rank sum', values: w.rankSums, strong: true },
		{ label: '− ' + nice(w.rBar), title: 'Rank sum minus m(n+1)/2', values: w.devs.map((d) => signed(d, 1)) },
		{ label: 'Squared', values: w.devs.map((d) => nice(d * d, 2)), foot: 'S = ' + nice(w.S, 2) }
	]}
/>
<p>
	<Term tip="The sum of the squared deviations of the rank sums from m(n+1)/2, shown at the bottom of the last column."><Tex tex="S" /></Term>
	measures how spread out the rank sums are. <Tex tex="W" /> divides <Tex tex="S" /> by the largest value it could take,
	<Tex tex={String.raw`\tfrac{1}{12} m^2(n^3 - n)`} />:
</p>
<Tex display tex={String.raw`W = \frac{S}{\tfrac{1}{12}\, m^2(n^3 - n)} = \frac{${tn(w.S, 2)}}{\tfrac{1}{12} \times ${m}^2 \times (${n}^3 - ${n})} = \frac{${tn(w.S, 2)}}{${tn(w.denom / 12, 1)}} = ${fx(w.W)}`} />
<Check label="W" tex="W" js={w.W} py={sheet.py.kendall_w} />
<p>
	<Tex tex="W" /> runs from 0 (no common ordering at all) to 1 (every judge gave the same ranking). One
	catch: if the judges ranked at random, <Tex tex="W" /> would still average <Tex tex={String.raw`\tfrac{1}{m}`} />,
	here <Tex tex={String.raw`\tfrac{1}{${m}} = ${fx(1 / m, 3)}`} />. So a bigger panel gets a lower
	<Tex tex="W" /> from chance alone, and <Tex tex="W" /> isn’t directly comparable across panel sizes.
</p>

<h4>Mean pairwise Spearman ρ</h4>
<p>
	<Term tip="Spearman’s rank correlation: 1 if two rankings are identical, −1 if one is the reverse of the other, about 0 if unrelated.">Spearman’s <Tex tex={String.raw`\rho`} /></Term>
	compares two judges’ rankings. For each competitor, take the difference <Tex tex="d" /> between the two
	ranks, and add up the squares, <Tex tex={String.raw`\sum d^2`} />. That’s 0 if the rankings are identical,
	and at most <Tex tex={String.raw`\tfrac{1}{3}\,n(n^2 - 1)`} />, when one ranking is the reverse of the other.
	ρ divides <Tex tex={String.raw`\sum d^2`} /> by that maximum and rescales it to run from 1 (identical) to
	−1 (reversed):
</p>
<Tex display tex={String.raw`\rho = 1 - 2 \times \frac{\sum d^2}{\tfrac{1}{3}\, n(n^2 - 1)}`} />
<p>Here it is for every pair of judges:</p>
<PairMatrix
	judges={sheet.judges}
	value={rho}
	fmt={(v) => minus(v.toFixed(3))}
	colour={(v) => agreeBg(v)}
	bind:selected
	label="Spearman’s ρ for each pair of judges"
>
	{#snippet detail(a, b)}
		<h4>J{a + 1} {sheet.judges[a]} and J{b + 1} {sheet.judges[b]}</h4>
		<div class="table-wrap">
			<table>
				<thead><tr><th>Competitor</th><th class="num">J{a + 1}</th><th class="num">J{b + 1}</th><th class="num">d</th><th class="num">d²</th></tr></thead>
				<tbody>
					{#each sheet.competitors as c, i (i)}
						<tr><td>{c}</td><td class="num">{sheet.R[a][i]}</td><td class="num">{sheet.R[b][i]}</td><td class="num">{signed(sp.d[i])}</td><td class="num">{sp.d[i] ** 2}</td></tr>
					{/each}
				</tbody>
				<tfoot><tr><td colspan="4">Σd²</td><td class="num">{sp.d2}</td></tr></tfoot>
			</table>
		</div>
		<Tex display tex={String.raw`\rho = 1 - 2 \times \frac{${sp.d2}}{\tfrac{1}{3} \times ${n} \times (${n}^2 - 1)} = 1 - 2 \times \frac{${sp.d2}}{${sp.denom / 3}} = ${fx(sp.rho)}`} />
	{/snippet}
</PairMatrix>
<p>The metric is the mean of these values over all {pairs.length} pairs of judges:</p>
<Tex display tex={String.raw`\bar\rho = \frac{1}{${pairs.length}} \sum_{\text{pairs}} \rho = \frac{${fx(pairSum)}}{${pairs.length}} = ${fx(pairMean)}`} />
<Check label="ρ̄" tex={String.raw`\bar\rho`} js={pairMean} py={sheet.py.mean_pairwise_rho} />
<p>
	Unlike <Tex tex="W" />, <Tex tex={String.raw`\bar\rho`} /> averages 0 if the judges rank at random, whatever
	the panel size, so it’s the fairer of the two for comparing panels of different sizes.
</p>
<aside class="aside small">
	<strong>A curiosity, and a cross-check:</strong> for rankings without ties, the mean pairwise ρ is exactly
	<Tex tex={String.raw`\frac{mW - 1}{m - 1}`} />, so for any one scoresheet it carries the same information
	as <Tex tex="W" />. The analysis code uses this as a shortcut:
	<Tex display tex={String.raw`\frac{mW - 1}{m - 1} = \frac{${m} \times ${fx(w.W, 6)} - 1}{${m} - 1} = ${fx(rhoBar)}`} />
	the same as the mean above.
</aside>

<style>
	.aside {
		border-left: 3px solid var(--border); background: var(--surface-2); color: var(--text-2);
		padding: 0.5em 0.9em; margin: 0.8em 0; max-width: 72ch;
	}
</style>
