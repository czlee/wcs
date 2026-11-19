<script>
	import RankMatrix from './RankMatrix.svelte';
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Term from './Term.svelte';
	import { kendallW, spearman, judgePairs } from '#lib/metrics.js';
	import { fx, nice, signed, minus } from '#lib/format.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet}} */
	let { sheet } = $props();
	const w = $derived(kendallW(sheet.R));
	const m = $derived(w.m), n = $derived(w.n);
	const rhoBar = $derived((m * w.W - 1) / (m - 1));
	const rho = (/** @type {number} */ a, /** @type {number} */ b) => spearman(sheet.R[a], sheet.R[b]).rho;
	const pairs = $derived(judgePairs(m));
	const pairMean = $derived(pairs.reduce((t, [a, b]) => t + rho(a, b), 0) / pairs.length);
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
	competitor’s sum would tend towards the same middle value, m(n + 1)/2 = {m}×{n + 1}/2 = <strong>{nice(w.rBar)}</strong>.
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
	<Term tip="The sum of the squared deviations of the rank sums from m(n+1)/2, shown at the bottom of the last column.">S</Term>
	measures how spread out the rank sums are. W divides S by the largest value it could take, m²(n³ − n)/12:
</p>
<p class="formula">
	W = 12 S / [m² (n³ − n)] = 12 × {nice(w.S, 2)} / [{m}² × ({n}³ − {n})] = {nice(12 * w.S, 2)} / {w.denom} = {fx(w.W)}
</p>
<Check label="W" js={w.W} py={sheet.py.kendall_w} />
<p>
	W runs from 0 (no common ordering at all) to 1 (every judge gave the same ranking). One catch: if the
	judges ranked at random, W would still average <strong>1/m</strong>, here 1/{m} = {fx(1 / m, 3)}. So a
	bigger panel gets a lower W from chance alone, and W isn’t directly comparable across panel sizes.
</p>

<h4>Mean pairwise Spearman ρ</h4>
<p>
	<Term tip="Spearman’s rank correlation: 1 if two rankings are identical, −1 if one is the reverse of the other, about 0 if unrelated.">Spearman’s ρ</Term>
	compares two judges’ rankings. For each competitor, take the difference d between the two ranks;
	then ρ = 1 − 6 Σd² / [n(n² − 1)]. Here it is for every pair of judges:
</p>
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
		<p class="formula">ρ = 1 − 6 × {sp.d2} / [{n} × ({n}² − 1)] = 1 − {6 * sp.d2} / {sp.denom} = {minus(fx(sp.rho))}</p>
	{/snippet}
</PairMatrix>
<p>
	The mean of these {pairs.length} values is {minus(fx(pairMean))}. For rankings without ties, that mean
	is exactly (mW − 1)/(m − 1), which is how the analysis computes it:
</p>
<p class="formula">ρ̄ = (mW − 1)/(m − 1) = ({m} × {fx(w.W)} − 1)/({m} − 1) = {minus(fx(rhoBar))}</p>
<Check label="ρ̄" js={rhoBar} py={sheet.py.mean_pairwise_rho} />
<p>
	So ρ̄ carries the same information as W for any one scoresheet, but on a scale that averages 0 under
	random judging whatever the panel size. That makes it the fairer of the two for comparing panels of
	different sizes.
</p>
