<script>
	import RankMatrix from './RankMatrix.svelte';
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Term from './Term.svelte';
	import Tex from './Tex.svelte';
	import { kendallW, spearman, judgePairs, spread } from '#lib/metrics.js';
	import { fx, nice, signed, minus } from '#lib/format.js';
	import { tn } from '#lib/tex.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	// Only the working of `focus` (a metric key) is shown, and it must make sense on its own.
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
	const s = $derived(spread(sheet.R));
	const f3 = (/** @type {number} */ v) => nice(v, 3);
	// Mean over competitors of the variance of their ranks, and what W says it must be.
	const meanVar = $derived(s.perCompetitor.reduce((t, c) => t + c.sd ** 2, 0) / n);
	const varFromW = $derived(((n * n - 1) / 12) * (1 - w.W));
</script>

<p class="lede small">
	This metric is built from <strong>squared</strong> rank gaps, so one
	big disagreement counts for more than several small ones adding up to the same number of places.
</p>

{#if focus === 'kendall_w'}
<h4>Kendall’s W, step by step</h4>
<p>
	This final has <Tex tex={`m = ${m}`} /> judges and <Tex tex={`n = ${n}`} /> competitors. Add up the ranks each
	competitor got from the {m} judges. If the judges agreed completely, these
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
{/if}

{#if focus === 'mean_pairwise_rho'}
<h4>Mean pairwise Spearman ρ</h4>
<p>
	<Term tip="Spearman’s rank correlation: 1 if two rankings are identical, −1 if one is the reverse of the other, about 0 if unrelated.">Spearman’s <Tex tex={String.raw`\rho`} /></Term>
	compares two judges’ rankings. For each competitor, take the difference <Tex tex="d" /> between the two
	ranks, and add up the squares, <Tex tex={String.raw`\sum d^2`} />. That’s 0 if the rankings are identical,
	and with <Tex tex={`n = ${n}`} /> competitors it’s at most
	<Tex tex={String.raw`\tfrac{1}{3}\,n(n^2 - 1) = ${sp.denom / 3}`} />, when one ranking is the reverse of the other.
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
<p>The metric, <Tex tex={String.raw`\bar\rho`} />, is the mean of these values over all {pairs.length} pairs of judges:</p>
<Tex display tex={String.raw`\bar\rho = \frac{1}{${pairs.length}} \sum_{\text{pairs}} \rho = \frac{${fx(pairSum)}}{${pairs.length}} = ${fx(pairMean)}`} />
<Check label="ρ̄" tex={String.raw`\bar\rho`} js={pairMean} py={sheet.py.mean_pairwise_rho} />
<p>
	If the judges ranked at random, <Tex tex={String.raw`\bar\rho`} /> would average 0, whatever the panel size, so
	panels of different sizes are compared fairly in that respect.
</p>
<aside class="aside small">
	<strong>A curiosity, and a cross-check:</strong> there’s a shortcut through Kendall’s <Tex tex="W" />, another
	of the metrics on this site, which measures how much the whole panel agrees on one order. For
	<Tex tex={`m = ${m}`} /> judges and rankings without ties, <Tex tex={String.raw`\bar\rho`} /> is exactly
	<Tex tex={String.raw`\frac{mW - 1}{m - 1}`} />, so for any one scoresheet the two carry the same information.
	Here <Tex tex={`W = ${fx(w.W, 6)}`} />, and the code behind the charts uses the shortcut:
	<Tex display tex={String.raw`\frac{mW - 1}{m - 1} = \frac{${m} \times ${fx(w.W, 6)} - 1}{${m} - 1} = ${fx(rhoBar)}`} />
	the same as the mean above.
</aside>
{/if}

{#if focus === 'sd_rank'}
<h4>Standard deviation of ranks</h4>
<p>
	This looks at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with
	ranks <Tex tex={String.raw`r_1, \dots, r_m`} /> and mean <Tex tex={String.raw`\bar r`} />, the standard
	deviation is
</p>
<Tex display tex={String.raw`\text{standard deviation} = \sqrt{\frac{1}{m}\sum_{j=1}^{m} (r_j - \bar r)^2}`} />
<p>
	(dividing by <Tex tex="m" />, not <Tex tex="m - 1" />). The metric is the average over the
	<Tex tex={`n = ${n}`} /> competitors.
	It’s in places, so lower means more agreement.
</p>
<RankMatrix
	{sheet}
	extras={[
		{ label: 'Mean', values: s.perCompetitor.map((c) => f3(c.mean)) },
		{ label: 'Standard deviation', title: 'Population standard deviation (÷ m)', values: s.perCompetitor.map((c) => f3(c.sd)), foot: f3(s.sd), strong: true }
	]}
/>
<p class="small muted">The bottom row of the last column is its average over competitors.</p>
<Check label="Standard deviation of ranks" js={s.sd} py={sheet.py.sd_rank} />
<p>
	Because it’s in places and isn’t scaled to the field size, it isn’t comparable across finals of different
	sizes: being 2 places apart in a field of {n} means more than in a field of 20.
</p>
<aside class="aside small">
	<strong>How this relates to Kendall’s W:</strong> Kendall’s <Tex tex="W" /> is another of the metrics on this
	site, which measures how much the whole panel agrees on one order; here <Tex tex={`W = ${fx(w.W, 6)}`} />. The
	squared standard deviations (the variances) carry the same information as <Tex tex="W" /> for a given field size. For rankings without ties, their average over competitors is exactly
	<Tex tex={String.raw`\tfrac{n^2 - 1}{12}(1 - W)`} />:
	<Tex display tex={String.raw`\tfrac{${n}^2 - 1}{12} \times (1 - ${fx(w.W, 6)}) = ${fx(varFromW)}, \quad \text{and the mean variance here is } ${fx(meanVar)}.`} />
	The metric averages the standard deviations rather than the variances, so it isn’t exactly a rescaling of <Tex tex="W" />,
	but it’s close.
</aside>
{/if}

<style>
	.lede { color: var(--text-2); }
</style>
