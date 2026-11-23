<script>
	import PairMatrix from './PairMatrix.svelte';
	import Check from './Check.svelte';
	import Tex from './Tex.svelte';
	import { kendallTau, judgePairs } from '#lib/metrics.js';
	import { fx, minus } from '#lib/format.js';
	import { tp } from '#lib/tex.js';
	import { agreeBg } from './agree.js';

	/** @type {{sheet: import('#lib/server/data.js').Sheet, focus: string}} */
	let { sheet, focus } = $props();
	// τ distance is worked out from τ̄, so its working includes τ̄'s. With `focus` on τ̄, the τ distance
	// part is dimmed.
	const m = $derived(sheet.judges.length), n = $derived(sheet.competitors.length);
	const pairs = $derived(judgePairs(m));
	const tau = (/** @type {number} */ a, /** @type {number} */ b) => kendallTau(sheet.R[a], sheet.R[b]).tau;
	const meanOf = (/** @type {(a: number, b: number) => number} */ f) => pairs.reduce((t, [a, b]) => t + f(a, b), 0) / pairs.length;
	const tauBar = $derived(meanOf(tau));
	const compPairs = $derived((n * (n - 1)) / 2);
	/** @type {[number, number]} */
	let selTau = $state([0, 1]);
	$effect(() => { if (selTau[1] >= m) selTau = [0, 1]; });
	const kt = $derived(kendallTau(sheet.R[selTau[0]], sheet.R[selTau[1]]));
	// Competitor indices, in the first judge's order, for the concordance grid.
	const order = $derived(sheet.competitors.map((_, i) => i).toSorted((x, y) => sheet.R[selTau[0]][x] - sheet.R[selTau[0]][y]));
</script>

{#if focus === 'tau_distance'}
	<p class="lede small">The τ distance is worked out from Kendall’s τ, so this starts with τ and converts it at the end.</p>
{/if}
<h4>Kendall’s τ, step by step</h4>
<p>
	Take two judges and any two competitors. If both judges put the same one of the two ahead, that
	competitor pair is <strong>concordant</strong>; if they disagree on who goes ahead, it’s
	<strong>discordant</strong>. With <Tex tex={`n = ${n}`} /> competitors there are
	<Tex tex={String.raw`\tfrac{n(n-1)}{2} = ${compPairs}`} /> competitor pairs, and
</p>
<Tex display tex={String.raw`\tau = \frac{\text{concordant} - \text{discordant}}{${compPairs}}`} />
<PairMatrix
	judges={sheet.judges}
	value={tau}
	fmt={(v) => minus(v.toFixed(3))}
	colour={(v) => agreeBg(v)}
	bind:selected={selTau}
	label="Kendall’s τ for each pair of judges"
>
	{#snippet detail(a, b)}
		<h4>J{a + 1} {sheet.judges[a]} and J{b + 1} {sheet.judges[b]}</h4>
		<p class="small">
			Competitors in J{a + 1}’s order (J{a + 1}’s rank / J{b + 1}’s rank). Each cell is one competitor pair:
			<span class="key agree">✓</span> concordant, <span class="key disagree">✗</span> discordant.
		</p>
		<div class="table-wrap">
			<table class="grid">
				<thead>
					<tr><th></th>{#each order as k, col (k)}{#if col > 0}<th class="num" title={sheet.competitors[k]}>{sheet.R[a][k]}/{sheet.R[b][k]}</th>{/if}{/each}</tr>
				</thead>
				<tbody>
					{#each order as i, row (i)}
						{#if row < order.length - 1}
							<tr>
								<th class="rh" title={sheet.competitors[i]}>{sheet.R[a][i]}/{sheet.R[b][i]} <span class="cn">{sheet.competitors[i]}</span></th>
								{#each order as k, col (k)}
									{#if col > 0}
										{#if col <= row}<td></td>
										{:else if kt.sign[i][k] > 0}<td class="agree" title="Concordant">✓</td>
										{:else}<td class="disagree" title="Discordant: J{a + 1} puts {sheet.competitors[i]} ahead, J{b + 1} puts {sheet.competitors[k]} ahead">✗</td>{/if}
									{/if}
								{/each}
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
		<Tex display tex={String.raw`\tau = \frac{${kt.C} - ${kt.D}}{${kt.pairs}} = ${fx(kt.tau)}`} />
	{/snippet}
</PairMatrix>
<p>
	The mean pairwise Kendall τ, written <Tex tex={String.raw`\bar\tau`} />, is the mean of
	<Tex tex={String.raw`\tau`} /> over all {pairs.length} pairs of judges:
</p>
<Check label="τ̄" tex={String.raw`\bar\tau`} js={tauBar} py={sheet.py.mean_pairwise_tau} />

<div class:dim={focus === 'mean_pairwise_tau'}>
<h4>{focus === 'mean_pairwise_tau' ? 'For comparison: Kendall τ distance' : 'Kendall τ distance'}</h4>
<p>
	The τ distance is <Tex tex={String.raw`\frac{1 - \bar\tau}{2}`} />. It’s the same information as
	<Tex tex={String.raw`\bar\tau`} />, turned around and rescaled: for a single pair of judges,
	<Tex tex={String.raw`\frac{1 - \tau}{2}`} /> is exactly the share of competitor pairs they order differently
	(discordant ÷ total). So it can be read as “on average, two judges disagree on
	{fx(((1 - tauBar) / 2) * 100, 0)}% of head-to-heads”. Lower is more agreement.
</p>
<Tex display tex={String.raw`\tau\text{ distance} = \frac{1 - \bar\tau}{2} = \frac{1 - ${tp(+fx(tauBar))}}{2} = ${fx((1 - tauBar) / 2)}`} />
<Check label="τ distance" tex={String.raw`\tau\text{ distance}`} js={(1 - tauBar) / 2} py={sheet.py.tau_distance} />
</div>

<style>
	.lede { color: var(--text-2); }
	.grid { font-size: 0.75rem; }
	.grid th, .grid td { padding: 0.1em 0.25em; text-align: center; }
	.grid .rh { text-align: left; white-space: nowrap; max-width: 9em; overflow: hidden; text-overflow: ellipsis; }
	@media (max-width: 600px) { .grid .cn { display: none; } }
	.grid .cn { font-weight: 400; color: var(--text-3); }
	.agree { background: var(--agree-bg); }
	.disagree { background: var(--disagree-bg); }
	.key { padding: 0 0.3em; border-radius: 3px; }
</style>
