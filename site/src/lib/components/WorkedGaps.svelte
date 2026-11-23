<script>
	import RankMatrix from './RankMatrix.svelte';
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import MetricLink from './MetricLink.svelte';
	import Tex from './Tex.svelte';
	import { spread, footrule, judgePairs } from '#lib/metrics.js';
	import { fx, nice } from '#lib/format.js';
	import { disagreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	// Only the working of `focus` (a metric key) is shown, except that the two MADs go together:
	// the other one is dimmed, and a note says what it is.
	const dim = (/** @type {string} */ k) => focus !== k;
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
	const MED = 'mean_abs_rank_dev_median', MEAN = 'mean_abs_rank_dev_mean';
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

{#if focus === MED || focus === MEAN}
<h4>Mean absolute deviation of each competitor’s ranks</h4>
<p>
	This looks at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with
	ranks <Tex tex={String.raw`r_1, \dots, r_m`} />, median <Tex tex={String.raw`\tilde r`} /> and mean
	<Tex tex={String.raw`\bar r`} />, take the average distance from the centre:
</p>
<div class="eqs">
	<div class:dim={dim(MED)}><Tex display tex={String.raw`\text{MAD (median)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \tilde r|`} /></div>
	<div class:dim={dim(MEAN)}><Tex display tex={String.raw`\text{MAD (mean)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \bar r|`} /></div>
</div>
<p>
	The metric is then the average over the {n} competitors. It’s in places, so lower means
	more agreement.
</p>
<p class="small muted">
	There are two versions: the mean absolute deviation (MAD) from the median, and from the mean. The one you’re
	looking at is from the {focus === MED ? 'median' : 'mean'}; the <MetricLink k={focus === MED ? MEAN : MED}>other</MetricLink> is dimmed, for comparison.
</p>
<RankMatrix
	{sheet}
	extras={[
		{ label: 'Median', values: s.perCompetitor.map((c) => nice(c.median, 1)), dim: dim(MED) },
		{ label: 'Mean', values: s.perCompetitor.map((c) => f3(c.mean)), dim: dim(MEAN) },
		{ label: 'MAD (median)', title: 'Mean absolute deviation from the median', values: s.perCompetitor.map((c) => f3(c.madMedian)), foot: f3(s.madMedian), strong: true, dim: dim(MED) },
		{ label: 'MAD (mean)', title: 'Mean absolute deviation from the mean', values: s.perCompetitor.map((c) => f3(c.madMean)), foot: f3(s.madMean), strong: true, dim: dim(MEAN) }
	]}
/>
<p class="small muted">The bottom row of each MAD column is its average over competitors.</p>
<div class:dim={dim(MED)}><Check label="Mean abs. rank deviation (median)" js={s.madMedian} py={sheet.py.mean_abs_rank_dev_median} /></div>
<div class:dim={dim(MEAN)}><Check label="Mean abs. rank deviation (mean)" js={s.madMean} py={sheet.py.mean_abs_rank_dev_mean} /></div>
<p>
	The median is the natural centre for absolute distances: no other point gives a smaller total. So {#if focus === MED}<MetricLink k={MEAN}>MAD (mean)</MetricLink>{:else}MAD (mean){/if}
	is never smaller than {#if focus === MEAN}<MetricLink k={MED}>MAD (median)</MetricLink>{:else}MAD (median){/if}, and it’s larger when one judge is far from the rest, because that judge
	pulls the mean (but not the median) towards them. Neither is scaled to the field size, so they aren’t
	comparable across finals of different sizes: being 2 places apart in a field of {n} means more
	than in a field of 20.
</p>
{/if}

<style>
	.lede { color: var(--text-2); }
</style>
