<script>
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Term from './Term.svelte';
	import MetricLink from './MetricLink.svelte';
	import Tex from './Tex.svelte';
	import { kendallTau, judgePairs } from '#lib/metrics.js';
	import { fx, minus } from '#lib/format.js';
	import { tp } from '#lib/tex.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	// τ̄ and the τ distance are parallel: both count concordant and discordant competitor pairs. Whichever
	// isn't `focus` is dimmed, for comparison.
	const isTau = $derived(focus === 'mean_pairwise_tau');
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const pairs = $derived(judgePairs(m));
	const tau = (/** @type {number} */ a, /** @type {number} */ b) => kendallTau(sheet.R[a], sheet.R[b]).tau;
	const meanOf = (/** @type {(a: number, b: number) => number} */ f) => pairs.reduce((t, [a, b]) => t + f(a, b), 0) / pairs.length;
	const dist = (/** @type {number} */ a, /** @type {number} */ b) => { const k = kendallTau(sheet.R[a], sheet.R[b]); return k.D / k.pairs; };
	const tauBar = $derived(meanOf(tau));
	const distBar = $derived(meanOf(dist));
	const compPairs = $derived((n * (n - 1)) / 2);
	/** @type {[number, number]} */
	let selTau = $state([0, 1]);
	$effect(() => { if (selTau[1] >= m) selTau = [0, 1]; });
	const kt = $derived(kendallTau(sheet.R[selTau[0]], sheet.R[selTau[1]]));
	// Competitor indices, in the first judge's order, for the concordance grid.
	const order = $derived(sheet.competitors.map((_, i) => i).toSorted((x, y) => sheet.R[selTau[0]][x] - sheet.R[selTau[0]][y]));
	// The competitor pair picked in the concordance grid, as positions (row, column) in the grid's order. Each
	// judge's choice of who goes ahead is highlighted in the ranks; it starts again whenever the judges or the scoresheet change.
	/** @type {[number, number]} */
	let hot = $state([0, 1]);
	$effect(() => { void sheet.id; void selTau[0]; void selTau[1]; hot = [0, 1]; });
	/** Whether judge j puts the grid's row competitor `row` ahead of the column competitor `col`. */
	const rowAhead = (/** @type {number} */ j, /** @type {number} */ row, /** @type {number} */ col) => sheet.R[j][order[row]] < sheet.R[j][order[col]];
</script>

<p class="lede">
	{#if !isTau}
		The <strong>Kendall <Tex tex={String.raw`\tau`} /> distance</strong> counts how many pairs of competitors in two judges’ rankings
		are different. Here we normalise it to a share of all pairs of competitors, from 0 to 1. The
		<strong>mean pairwise normalised</strong> Kendall <Tex tex={String.raw`\tau`} /> distance averages this over every pair of judges on the panel.
	{:else}
		The <strong>Kendall rank correlation coefficient</strong>, often known as <strong>Kendall’s <Tex tex={String.raw`\tau`} /></strong>,
		counts how many pairs of competitors in two judges’ rankings are the same and different. The
		<strong>mean pairwise</strong> Kendall rank correlation coefficient averages this over every pair of judges on the panel.
	{/if}
</p>
<p class="small muted">
	The metric you’re looking at is the {isTau ? 'mean pairwise Kendall correlation' : 'mean pairwise normalised Kendall τ distance'}. The
	{#if isTau}<MetricLink k="tau_distance">mean pairwise normalised Kendall τ distance</MetricLink>{:else}<MetricLink k="mean_pairwise_tau">mean pairwise Kendall correlation</MetricLink>{/if} is dimmed, for comparison.
</p>
<p class="small muted">
	Since both metrics are based on Kendall’s <Tex tex={String.raw`\tau`} />, the notation can get confusing. We’ll use
	<Tex tex={String.raw`\tau`} /> for the correlation coefficient, and <Tex tex={String.raw`d_\tau`} /> for the distance.
	Each is worked out for a pair of judges <Tex tex="J_i" /> and <Tex tex="J_j" />, so we write
	<Tex tex={String.raw`\tau(J_i, J_j)`} /> and <Tex tex={String.raw`d_\tau(J_i, J_j)`} />. A bar, as in <Tex tex={String.raw`\bar\tau`} /> and <Tex tex={String.raw`\bar d_\tau`} />, means the mean over every pair of judges.
</p>
<h4>Concordant and discordant pairs</h4>
<p>
	Take two judges and any two competitors. If both judges put the same competitor ahead, that
	competitor pair is <strong>concordant</strong>; if they disagree on who goes ahead, it’s
	<strong>discordant</strong>. With <Tex tex={`n = ${n}`} /> competitors there are
	<Tex tex={String.raw`\tfrac{n(n-1)}{2} = ${compPairs}`} /> competitor pairs. For each pair of judges:
</p>
<div class="side">
	<div class:dim={isTau}><Tex display tex={String.raw`d_\tau(J_i, J_j) = \frac{\text{discordant}}{${compPairs}}`} /></div>
	<div class:dim={!isTau}><Tex display tex={String.raw`\tau(J_i, J_j) = \frac{\text{concordant} - \text{discordant}}{${compPairs}}`} /></div>
</div>
<PairMatrix
	select="click"
	judges={sheet.judges}
	value={isTau ? tau : dist}
	fmt={(v) => (isTau ? minus(v.toFixed(3)) : v.toFixed(3))}
	colour={(v) => agreeBg(isTau ? v : 1 - 2 * v)}
	bind:selected={selTau}
	label={isTau ? 'Kendall’s τ for each pair of judges' : 'Share of competitor pairs ordered differently, for each pair of judges'}
>
	{#snippet detail(a, b)}
		<h4>J{a + 1} {sheet.judges[a]} and J{b + 1} {sheet.judges[b]}</h4>
		<p class="small">
			Competitors in J{a + 1}’s order, with both judges’ ranks for each along the top and down the left. Each cell is one competitor pair:
			<span class="key agree">✓</span> concordant, <span class="key disagree">✗</span> discordant. Hover over or tap a cell to
			see how a pair is concordant or discordant.
		</p>
		{@const ci = order[hot[0]]}
		{@const ck = order[hot[1]]}
		{@const aFirst = rowAhead(a, hot[0], hot[1]) ? ci : ck}
		{@const bFirst = rowAhead(b, hot[0], hot[1]) ? ci : ck}
		{@const same = aFirst === bFirst}
		<p class="verdict" class:agree={same} class:disagree={!same} aria-live="polite">
			{#if same}
				J{a + 1} and J{b + 1} both put <strong>{sheet.competitors[aFirst]}</strong> ahead of
				<strong>{sheet.competitors[aFirst === ci ? ck : ci]}</strong>, so this competitor pair is concordant <span class="mark">✓</span>
			{:else}
				J{a + 1} put <strong>{sheet.competitors[aFirst]}</strong> ahead, but J{b + 1} put
				<strong>{sheet.competitors[bFirst]}</strong> ahead, so this competitor pair is discordant <span class="mark">✗</span>
			{/if}
		</p>
		<div class="table-wrap">
			<table class="grid">
				<thead>
					<tr class="initials">
						<th colspan="3"></th>
						{#each order as k, col (k)}{#if col > 0}<th class="ini"><Term tip={sheet.competitors[k]} plain>{Array.from(sheet.competitors[k].trim())[0] ?? ''}</Term></th>{/if}{/each}
					</tr>
					<tr>
						<th class="lab ja" colspan="3">J{a + 1}’s rank</th>
						{#each order as k, col (k)}{#if col > 0}<th class="rk ja" class:ahead={hot[1] === col && !rowAhead(a, hot[0], col)} class:behind={hot[1] === col && rowAhead(a, hot[0], col)}>{sheet.R[a][k]}</th>{/if}{/each}
					</tr>
					<tr>
						<th class="lab jb" colspan="3">J{b + 1}’s rank</th>
						{#each order as k, col (k)}{#if col > 0}<th class="rk jb" class:ahead={hot[1] === col && !rowAhead(b, hot[0], col)} class:behind={hot[1] === col && rowAhead(b, hot[0], col)}>{sheet.R[b][k]}</th>{/if}{/each}
					</tr>
					<tr class="heads">
						<th class="cn0">Competitor</th><th class="rk0 ja">J{a + 1}</th><th class="rk0 jb">J{b + 1}</th><th colspan={n - 1}></th>
					</tr>
				</thead>
				<tbody>
					{#each order as i, row (i)}
						{#if row < order.length - 1}
							<tr>
								<th class="rh"><span class="cn"><Term tip={sheet.competitors[i]} plain>{sheet.competitors[i]}</Term></span></th>
								<td class="rk ja" class:ahead={hot[0] === row && rowAhead(a, row, hot[1])} class:behind={hot[0] === row && !rowAhead(a, row, hot[1])}>{sheet.R[a][i]}</td>
								<td class="rk jb" class:ahead={hot[0] === row && rowAhead(b, row, hot[1])} class:behind={hot[0] === row && !rowAhead(b, row, hot[1])}>{sheet.R[b][i]}</td>
								{#each order as k, col (k)}
									{#if col > 0}
										{#if col <= row}<td></td>
										{:else}
											{@const conc = kt.sign[i][k] > 0}
											{@const picked = hot[0] === row && hot[1] === col}
											<td class={conc ? 'agree' : 'disagree'} class:hot={picked} role="button" tabindex="0" aria-pressed={picked}
												aria-label="{sheet.competitors[i]} and {sheet.competitors[k]}: {conc ? 'concordant' : 'discordant'}"
												onmouseenter={() => (hot = [row, col])} onfocus={() => (hot = [row, col])} onclick={() => (hot = [row, col])}
												onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); hot = [row, col]; } }}>{conc ? '✓' : '✗'}</td>
										{/if}
									{/if}
								{/each}
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
		<div class="side">
			<div class:dim={isTau}><Tex display tex={String.raw`d_\tau(J_{${a + 1}}, J_{${b + 1}}) = \frac{${kt.D}}{${kt.pairs}} = ${fx(kt.D / kt.pairs)}`} /></div>
			<div class:dim={!isTau}><Tex display tex={String.raw`\tau(J_{${a + 1}}, J_{${b + 1}}) = \frac{${kt.C} - ${kt.D}}{${kt.pairs}} = ${fx(kt.tau)}`} /></div>
		</div>
	{/snippet}
</PairMatrix>
<div class:dim={isTau}>
	<p>
		The <strong>mean pairwise normalised Kendall <Tex tex={String.raw`\tau`} /> distance</strong>, written <Tex tex={String.raw`\bar d_\tau`} />, is the mean of
		<Tex tex={String.raw`d_\tau`} /> over all {pairs.length} pairs of judges. It reads as “on average, two judges
		order {fx(distBar * 100, 0)}% of head-to-heads differently”.
	</p>
	<Check display label="d̄τ" tex={String.raw`\bar d_\tau = \frac{1}{${pairs.length}} \sum_{i<j} d_\tau(J_i, J_j)`} js={distBar} py={sheet.py.tau_distance} />
</div>
<div class:dim={!isTau}>
	<p>
		The <strong>mean pairwise Kendall correlation</strong>, written <Tex tex={String.raw`\bar\tau`} />, is the mean of
		<Tex tex={String.raw`\tau`} /> over all {pairs.length} pairs of judges.
	</p>
	<Check display label="τ̄" tex={String.raw`\bar\tau = \frac{1}{${pairs.length}} \sum_{i<j} \tau(J_i, J_j)`} js={tauBar} py={sheet.py.mean_pairwise_tau} />
</div>

<aside class="aside small">
	<strong>A curiosity:</strong> Every pair of competitors is either concordant or discordant, so
	<Tex tex={String.raw`\text{concordant} = ${compPairs} - \text{discordant}`} /> and the two metrics are linked:
	<Tex display tex={String.raw`\bar d_\tau = \frac{1 - \bar\tau}{2} \qquad \left(\text{here: } ${fx((1 - tauBar) / 2)} = \frac{1 - ${tp(+fx(tauBar))}}{2}\right)`} />
	So each is a reversed and scaled version of the other:
	<div class="scales">
		<span></span>
		<div class="ends"><span>perfect disagreement</span><span>random judging</span><span>perfect agreement</span></div>
		<span class="lab"><Tex tex={String.raw`\bar d_\tau`} /></span>
		<div class="bar"><b class="v">1</b><b class="v">0.5</b><b class="v">0</b></div>
		<span class="lab"><Tex tex={String.raw`\bar\tau`} /></span>
		<div class="bar"><b class="v">{minus('-1')}</b><b class="v">0</b><b class="v">1</b></div>
	</div>
</aside>

<style>
	.scales { display: grid; grid-template-columns: auto 1fr; gap: 0.35em 0.9em; align-items: center; margin: 0.7em 0 0.2em; max-width: 34em; }
	.scales .ends { display: grid; grid-template-columns: 1fr auto 1fr; font-size: 0.85em; color: var(--text-3); }
	.scales .ends span:nth-child(2) { text-align: center; }
	.scales .ends span:last-child { text-align: right; }
	.scales .lab { text-align: right; }
	.scales .bar {
		display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; text-align: center;
		height: 1.7em; padding: 0 0.6em; border-radius: 999px;
		background: linear-gradient(to right, color-mix(in srgb, var(--bad) 55%, transparent), color-mix(in srgb, var(--grid) 70%, transparent), color-mix(in srgb, var(--ok) 55%, transparent));
	}
	.scales .bar b:first-child { text-align: left; }
	.scales .bar b:last-child { text-align: right; }
	.scales .v { font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
	.side { display: flex; flex-wrap: wrap; justify-content: flex-start; align-items: baseline; gap: 0 1.5em; }
	.grid { font-size: 0.75rem; }
	.grid th, .grid td { padding: 0.1em 0.25em; text-align: center; }
	.grid .rh { text-align: left; white-space: nowrap; max-width: 9em; overflow: hidden; text-overflow: ellipsis; }
	.grid .rh :global(.wrap), .grid .rh :global(.term) { display: block; max-width: 9em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: left; }
	@media (max-width: 600px) { .grid .cn { display: none; } }
	.grid .cn { font-weight: 400; color: var(--text-3); }
	.grid .lab { text-align: right; font-weight: 400; color: var(--text-2); padding-right: 0.6em; }
	.grid .rk { min-width: 1.8em; }
	.grid .ini { font-weight: 400; color: var(--text-3); }
	.verdict { padding: 0.35em 0.6em; border-radius: 4px; margin: 0.4em 0; }
	.verdict .mark { font-weight: 700; margin-left: 0.2em; }
	.grid td[role='button'] { cursor: pointer; }
	.grid td.hot { outline: 2px solid var(--highlight); outline-offset: -2px; }
	/* Each judge has a colour: strong for the competitor they put ahead in the picked pair, light for the one behind. */
	.grid .ja { --hue: var(--judge-a); }
	.grid .jb { --hue: var(--judge-b); }
	.grid .rk.behind { background: color-mix(in srgb, var(--hue) 11%, transparent); }
	.grid .rk.ahead { background: color-mix(in srgb, var(--hue) 55%, transparent); font-weight: 700; }
	.grid .lab { box-shadow: inset -3px 0 0 var(--hue); }
	.grid .heads .rk0 { border-bottom: 3px solid var(--hue); }
	.grid thead .rk { font-weight: 400; }
	.grid .heads th { font-weight: 600; text-align: center; border-bottom: 1px solid var(--border); }
	.grid .heads .cn0 { text-align: left; }
	.agree { background: var(--agree-bg); }
	.disagree { background: var(--disagree-bg); }
	.key { padding: 0 0.3em; border-radius: 3px; }
</style>
