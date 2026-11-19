<script>
	import RankMatrix from './RankMatrix.svelte';
	import Check from './Check.svelte';
	import Tex from './Tex.svelte';
	import { spread } from '#lib/metrics.js';
	import { nice } from '#lib/format.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();
	const s = $derived(spread(sheet.R));
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const f3 = (/** @type {number} */ v) => nice(v, 3);
</script>

<p>
	These look at each competitor in turn: how far apart are the {m} ranks they got? For a competitor with
	ranks <Tex tex={String.raw`r_1, \dots, r_m`} />, mean <Tex tex={String.raw`\bar r`} /> and median
	<Tex tex={String.raw`\tilde r`} />:
</p>
<Tex display tex={String.raw`\text{MAD (mean)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \bar r| \qquad \text{MAD (median)} = \frac{1}{m}\sum_{j=1}^{m} |r_j - \tilde r| \qquad \text{SD} = \sqrt{\frac{1}{m}\sum_{j=1}^{m} (r_j - \bar r)^2}`} />
<p>
	(The SD divides by <Tex tex="m" />, not <Tex tex="m - 1" />.) Each metric is then the average over the
	{n} competitors. All three are in places, so lower means more agreement.
</p>
<RankMatrix
	{sheet}
	extras={[
		{ label: 'Mean', values: s.perCompetitor.map((c) => f3(c.mean)) },
		{ label: 'Median', values: s.perCompetitor.map((c) => nice(c.median, 1)) },
		{ label: 'MAD (mean)', title: 'Mean absolute deviation from the mean', values: s.perCompetitor.map((c) => f3(c.madMean)), foot: f3(s.madMean), strong: true },
		{ label: 'MAD (median)', title: 'Mean absolute deviation from the median', values: s.perCompetitor.map((c) => f3(c.madMedian)), foot: f3(s.madMedian), strong: true },
		{ label: 'SD', title: 'Standard deviation (population, ÷ m)', values: s.perCompetitor.map((c) => f3(c.sd)), foot: f3(s.sd), strong: true }
	]}
/>
<p class="small muted">The bottom row of each of the last three columns is its average over competitors.</p>
<Check label="Mean abs. rank deviation (mean)" js={s.madMean} py={sheet.py.mean_abs_rank_dev_mean} />
<Check label="Mean abs. rank deviation (median)" js={s.madMedian} py={sheet.py.mean_abs_rank_dev_median} />
<Check label="SD of ranks" js={s.sd} py={sheet.py.sd_rank} />
<p>
	These are in places and aren’t scaled to the field size, so they aren’t comparable across finals of
	different sizes: being 2 places apart in a field of {n} means more than in a field of 20. The three are
	usually close to each other; they differ in how much weight they give one judge who is far from the rest.
</p>
