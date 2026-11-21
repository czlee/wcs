<script>
	import RankMatrix from './RankMatrix.svelte';
	import Check from './Check.svelte';
	import Tex from './Tex.svelte';
	import { spread } from '#lib/metrics.js';
	import { nice } from '#lib/format.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus?: string}} */
	let { sheet, focus } = $props();
	// With `focus` (a metric key), only that metric's working is shown; without it, all three.
	const on = (/** @type {string} */ k) => !focus || focus === k;
	const s = $derived(spread(sheet.R));
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const f3 = (/** @type {number} */ v) => nice(v, 3);
</script>

<p>
	{focus ? 'This looks' : 'These look'} at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with
	ranks <Tex tex={String.raw`r_1, \dots, r_m`} />, mean <Tex tex={String.raw`\bar r`} /> and median
	<Tex tex={String.raw`\tilde r`} />:
</p>
<Tex display tex={[
	on('mean_abs_rank_dev_mean') && String.raw`\text{MAD (mean)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \bar r|`,
	on('mean_abs_rank_dev_median') && String.raw`\text{MAD (median)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \tilde r|`,
	on('sd_rank') && String.raw`\text{SD} = \sqrt{\frac{1}{m}\sum_{j=1}^{m} (r_j - \bar r)^2}`
].filter(Boolean).join(String.raw` \qquad `)} />
<p>
	{#if on('sd_rank')}(The SD divides by <Tex tex="m" />, not <Tex tex="m - 1" />.){/if}
	{focus ? 'The metric' : 'Each metric'} is then the average over the {n} competitors.
	{focus ? 'It’s' : 'All three are'} in places, so lower means more agreement.
</p>
<RankMatrix
	{sheet}
	extras={[
		(on('mean_abs_rank_dev_mean') || on('sd_rank')) && { label: 'Mean', values: s.perCompetitor.map((c) => f3(c.mean)) },
		on('mean_abs_rank_dev_median') && { label: 'Median', values: s.perCompetitor.map((c) => nice(c.median, 1)) },
		on('mean_abs_rank_dev_mean') && { label: 'MAD (mean)', title: 'Mean absolute deviation from the mean', values: s.perCompetitor.map((c) => f3(c.madMean)), foot: f3(s.madMean), strong: true },
		on('mean_abs_rank_dev_median') && { label: 'MAD (median)', title: 'Mean absolute deviation from the median', values: s.perCompetitor.map((c) => f3(c.madMedian)), foot: f3(s.madMedian), strong: true },
		on('sd_rank') && { label: 'SD', title: 'Standard deviation (population, ÷ m)', values: s.perCompetitor.map((c) => f3(c.sd)), foot: f3(s.sd), strong: true }
	].filter((e) => !!e)}
/>
<p class="small muted">{focus ? 'The bottom row of the last column is its' : 'The bottom row of each of the last three columns is its'} average over competitors.</p>
{#if on('mean_abs_rank_dev_mean')}<Check label="Mean abs. rank deviation (mean)" js={s.madMean} py={sheet.py.mean_abs_rank_dev_mean} />{/if}
{#if on('mean_abs_rank_dev_median')}<Check label="Mean abs. rank deviation (median)" js={s.madMedian} py={sheet.py.mean_abs_rank_dev_median} />{/if}
{#if on('sd_rank')}<Check label="SD of ranks" js={s.sd} py={sheet.py.sd_rank} />{/if}
<p>
	These are in places and aren’t scaled to the field size, so they aren’t comparable across finals of
	different sizes: being 2 places apart in a field of {n} means more than in a field of 20.{#if !focus} The three are
	usually close to each other; they differ in how much weight they give one judge who is far from the rest.{/if}
</p>
