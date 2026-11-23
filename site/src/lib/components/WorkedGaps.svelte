<script>
	import RankMatrix from './RankMatrix.svelte';
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Tex from './Tex.svelte';
	import { spread, madScale, footrule, judgePairs } from '#lib/metrics.js';
	import { fx, nice } from '#lib/format.js';
	import { disagreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const pairs = $derived(judgePairs(m));
	const fr = (/** @type {number} */ a, /** @type {number} */ b) => footrule(sheet.R[a], sheet.R[b]).value;
	const frBar = $derived(pairs.reduce((t, [a, b]) => t + fr(a, b), 0) / pairs.length);
	/** @type {[number, number]} */
	let selFr = $state([0, 1]);
	$effect(() => { if (selFr[1] >= m) selFr = [0, 1]; });
	const ft = $derived(footrule(sheet.R[selFr[0]], sheet.R[selFr[1]]));
	const s = $derived(spread(sheet.R));
	const f3 = (/** @type {number} */ v) => nice(v, 3);
	const scale = $derived(madScale(n));
	const MED = 'mean_abs_rank_dev_median_norm';
</script>

<p class="lede small">
	This metric counts rank gaps in plain places, so a gap of 4 places
	counts the same as four gaps of 1 place.
</p>

{#if focus === 'footrule_mean'}
<h4>Spearman’s footrule</h4>
<p>
	The footrule adds up how many places apart two judges put each competitor, and divides by the largest
	total possible, which for <Tex tex={`n = ${n}`} /> competitors is <Tex tex={String.raw`\lfloor n^2/2 \rfloor = \lfloor ${n}^2/2 \rfloor = ${Math.floor((n * n) / 2)}`} />
	(when one ranking is the reverse of the other). 0 means identical rankings, 1 means as different as
	possible. Lower is more agreement.
</p>
<Tex display tex={String.raw`\text{footrule} = \frac{\sum_i |r_{a,i} - r_{b,i}|}{\lfloor n^2/2 \rfloor}`} />
<PairMatrix
	judges={sheet.judges}
	value={fr}
	fmt={(v) => v.toFixed(3)}
	colour={(v) => disagreeBg(2 * v)}
	bind:selected={selFr}
	label="Normalised footrule for each pair of judges"
>
	{#snippet detail(a, b)}
		<h4>J{a + 1} {sheet.judges[a]} and J{b + 1} {sheet.judges[b]}</h4>
		<div class="table-wrap">
			<table>
				<thead><tr><th>Competitor</th><th class="num">J{a + 1}</th><th class="num">J{b + 1}</th><th class="num">|diff|</th></tr></thead>
				<tbody>
					{#each sheet.competitors as c, i (i)}
						<tr><td>{c}</td><td class="num">{sheet.R[a][i]}</td><td class="num">{sheet.R[b][i]}</td><td class="num">{ft.absDiff[i]}</td></tr>
					{/each}
				</tbody>
				<tfoot><tr><td colspan="3">Total</td><td class="num">{ft.total}</td></tr></tfoot>
			</table>
		</div>
		<Tex display tex={String.raw`\text{footrule} = \frac{${ft.total}}{${ft.max}} = ${fx(ft.value)}`} />
	{/snippet}
</PairMatrix>
<p>The metric is the mean of the footrule over all {pairs.length} pairs of judges:</p>
<Check label="Mean footrule" js={frBar} py={sheet.py.footrule_mean} />
{/if}

{#if focus === MED}
<h4>Mean absolute deviation of each competitor’s ranks</h4>
<p>
	This looks at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with
	ranks <Tex tex={String.raw`r_1, \dots, r_m`} /> and median <Tex tex={String.raw`\tilde r`} />, take the average
	distance from the median:
</p>
<Tex display tex={String.raw`\text{mean absolute deviation} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \tilde r|`} />
<p>
	The median is the natural centre for absolute distances: no other point gives a smaller total.
	The metric starts from the average over the {n} competitors. That’s in places, so lower means more agreement.
</p>
<RankMatrix
	{sheet}
	extras={[
		{ label: 'Median', values: s.perCompetitor.map((c) => nice(c.median, 1)) },
		{ label: 'Mean abs. dev.', title: 'Mean absolute deviation from the median', values: s.perCompetitor.map((c) => f3(c.madMedian)), foot: f3(s.madMedian), strong: true }
	]}
/>
<p class="small muted">The bottom row of the last column is its average over competitors, in places.</p>
<p>
	<strong>Normalising.</strong> Because the average is in places, it can’t be compared across finals of different sizes. So the
	metric normalises it, dividing by <Tex tex={String.raw`n/4`} />, which is what the average would be if half the
	panel ranked in order and half in exact reverse. No panel can go above it. Then 0 means every judge agreed on every
	competitor, and 1 means the panel was split as far as it could be. A panel with an odd number of finalists or judges
	can’t quite reach it, so the most split such a panel can look is a little under 1.
</p>
<Tex display tex={String.raw`\frac{${f3(s.madMedian)}}{n/4} = \frac{${f3(s.madMedian)}}{${n}/4} = \frac{${f3(s.madMedian)}}{${nice(scale, 3)}} = ${fx(s.madMedian / scale)}`} />
<Check label="Mean absolute deviation, normalised" js={s.madMedian / scale} py={sheet.py.mean_abs_rank_dev_median_norm} />
<p class="small muted">
	Normalising this way is a first pass. It removes the main effect of field size, but not all of it:
	random rankings don’t land at the same value for every field and panel size, so a chance-based correction is planned.
</p>
{/if}

<style>
	.lede { color: var(--text-2); }
</style>
