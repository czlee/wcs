<script>
	// A scoresheet's ranks: one row per competitor (in the scoresheet's order), one
	// column per judge, then any extra computed columns. Cells are shaded by rank
	// (1st darkest). `highlight` picks out judges' columns; `rowHighlight`, competitors' rows.
	/** @typedef {{label: string, values: (string|number)[], foot?: string, title?: string, strong?: boolean}} Extra */
	/**
	 * @type {{sheet: {judges: string[], competitors: string[], R: number[][]}, extras?: Extra[],
	 *   highlight?: number[], rowHighlight?: number[], caption?: string}}
	 */
	let { sheet, extras = [], highlight = [], rowHighlight = [], caption = '' } = $props();
	const m = $derived(sheet.judges.length);
	const n = $derived(sheet.competitors.length);
	/** Shade for rank r of n: 1st is strongest. */
	const shade = (/** @type {number} */ r) => `color-mix(in srgb, var(--accent) ${Math.round(70 * (1 - (r - 1) / Math.max(n - 1, 1)))}%, transparent)`;
	const hasFoot = $derived(extras.some((e) => e.foot !== undefined));
</script>

<div class="table-wrap">
	<table class="ranks">
		{#if caption}<caption>{caption}</caption>{/if}
		<thead>
			<tr>
				<th class="comp">Competitor</th>
				{#each sheet.judges as j, k (k)}
					<th class="judge" class:hl={highlight.includes(k)} title={j}><span class="jn">J{k + 1}</span><span class="name">{j}</span></th>
				{/each}
				{#each extras as e, k (k)}<th class="num extra" title={e.title}>{e.label}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each sheet.competitors as c, i (i)}
				<tr class:rowhl={rowHighlight.includes(i)}>
					<td class="comp">{c}</td>
					{#each sheet.R as row, k (k)}
						<td class="rank num" class:hl={highlight.includes(k)} style:--shade={shade(row[i])}>{row[i]}</td>
					{/each}
					{#each extras as e, k (k)}<td class="num extra" class:strong={e.strong}>{e.values[i]}</td>{/each}
				</tr>
			{/each}
		</tbody>
		{#if hasFoot}
			<tfoot>
				<tr>
					<td class="comp" colspan={m + 1}>{m} judges × {n} competitors</td>
					{#each extras as e, k (k)}<td class="num extra">{e.foot ?? ''}</td>{/each}
				</tr>
			</tfoot>
		{/if}
	</table>
</div>
<p class="key small muted">{#each sheet.judges as j, k (k)}{k > 0 ? ' · ' : ''}<span class:hlk={highlight.includes(k)}>J{k + 1} {j}</span>{/each}</p>

<style>
	/* Narrow screens: judge names go in a key under the table instead of the column headers. */
	.key { display: none; margin-top: -0.3em; }
	.hlk { background: var(--highlight-bg); }
	@media (max-width: 600px) {
		.key { display: block; }
		.judge .name { display: none !important; }
		.comp { min-width: 8em; }
	}
	.ranks { font-size: 0.85rem; }
	caption { text-align: left; color: var(--text-2); font-size: 0.85rem; padding-bottom: 0.3em; }
	.comp { min-width: 11em; max-width: 18em; }
	th.judge { text-align: center; vertical-align: top; padding-inline: 0.3em; max-width: 5.5em; }
	.judge .jn { display: block; color: var(--text); }
	.judge .name { display: block; font-weight: 400; font-size: 0.72rem; line-height: 1.15; color: var(--text-3); }
	td.rank { text-align: center; background: var(--shade); min-width: 2.4em; }
	.hl { outline: 2px solid var(--highlight); outline-offset: -2px; }
	th.hl { background: var(--highlight-bg); }
	tr.rowhl td { background-color: var(--highlight-bg); }
	tr.rowhl td.rank { background: linear-gradient(var(--shade), var(--shade)), var(--highlight-bg); }
	.extra { border-left: 1px solid var(--border); }
	.extra + .extra { border-left: 0; }
	.strong { font-weight: 600; }
	tfoot td.comp { font-weight: 400; color: var(--text-3); }
</style>
