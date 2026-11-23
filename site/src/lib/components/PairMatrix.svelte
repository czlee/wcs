<script>
	// A judge × judge matrix of one pairwise value. Hovering, focusing or tapping a
	// cell selects that pair, and `detail` renders its working beside the matrix. A working with
	// hover content of its own (tooltips) sets `select="click"`, so the pointer can cross the matrix
	// to the working without changing the pair on the way.
	// Modelled on the Schulze tables at whowouldawon.dance.
	/**
	 * @type {{judges: string[], value: (a: number, b: number) => number, fmt: (v: number) => string,
	 *   colour?: (v: number) => string, selected: [number, number],
	 *   detail: import('svelte').Snippet<[number, number]>, label: string, select?: 'hover' | 'click'}}
	 */
	let { judges, value, fmt, colour = () => 'transparent', selected = $bindable(), detail, label, select = 'hover' } = $props();
	const pick = (/** @type {number} */ a, /** @type {number} */ b) => {
		if (a !== b) selected = a < b ? [a, b] : [b, a];
	};
	const isSel = (/** @type {number} */ a, /** @type {number} */ b) =>
		(a === selected[0] && b === selected[1]) || (a === selected[1] && b === selected[0]);
</script>

<div class="pm">
	<div class="table-wrap matrix">
		<table aria-label={label}>
			<thead>
				<tr>
					<th></th>
					{#each judges as j, b (b)}<th class="num colhead" class:on={b === selected[0] || b === selected[1]} title={j}>J{b + 1}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each judges as j, a (a)}
					<tr>
						<th class="rowhead" class:on={a === selected[0] || a === selected[1]} title={j}>J{a + 1} <span class="name">{j}</span></th>
						{#each judges as _, b (b)}
							{#if a === b}
								<td class="diag">—</td>
							{:else}
								{@const v = value(a, b)}
								<td class="num cell" class:sel={isSel(a, b)} style:--bg={colour(v)}>
									<button type="button" aria-pressed={isSel(a, b)} aria-label="J{a + 1} and J{b + 1}: {fmt(v)}"
										onmouseenter={() => select === 'hover' && pick(a, b)} onfocus={() => pick(a, b)} onclick={() => pick(a, b)}>{fmt(v)}</button>
								</td>
							{/if}
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<p class="small muted hint">{select === 'click' ? 'Click' : 'Hover over'} or tap a cell to see that pair’s working.</p>
	</div>
	<div class="detail" aria-live="polite">
		{@render detail(selected[0], selected[1])}
	</div>
</div>

<style>
	.pm { display: grid; grid-template-columns: minmax(0, auto) minmax(0, 1fr); gap: 1.2em; align-items: start; margin: 0.6em 0; }
	@media (max-width: 760px) { .pm { grid-template-columns: minmax(0, 1fr); } }
	.matrix table { font-size: 0.8rem; }
	.matrix th, .matrix td { padding: 0.15em 0.3em; }
	.rowhead { white-space: nowrap; font-weight: 600; max-width: 12em; overflow: hidden; text-overflow: ellipsis; }
	.rowhead .name { font-weight: 400; color: var(--text-3); }
	.rowhead.on, .colhead.on { background: var(--highlight-bg); }
	.diag { color: var(--text-3); text-align: center; }
	td.cell { background: var(--bg); padding: 0; }
	td.cell button {
		font: inherit; color: inherit; background: none; border: 0; padding: 0.15em 0.35em; width: 100%;
		cursor: pointer; font-variant-numeric: tabular-nums; text-align: right;
	}
	td.cell.sel { outline: 2px solid var(--highlight); outline-offset: -2px; font-weight: 700; }
	.hint { margin-top: 0.2em; }
	.detail {
		border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2);
		padding: 0.5em 0.8em; min-width: 0; font-size: 0.88rem;
	}
	.detail :global(h4) { margin-top: 0.2em; }
	.detail :global(table) { font-size: 0.8rem; }
</style>
