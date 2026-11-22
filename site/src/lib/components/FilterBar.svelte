<script>
	// Toggle buttons that narrow the scoresheets shown, one group per dimension. Several
	// bins of a dimension can be on at once; none on means no filter. `filters` is bindable.
	import { DIMENSIONS, anyFilters, noFilters } from '#lib/dimensions.js';
	import Term from './Term.svelte';

	/** @type {{filters: import('#lib/dimensions.js').Filters}} */
	let { filters = $bindable() } = $props();

	const toggle = (/** @type {import('#lib/dimensions.js').Dimension} */ d, /** @type {string} */ id) => {
		const on = filters[d.id];
		// Kept in bin order, so the URL doesn't depend on the order of clicks.
		const next = on.includes(id) ? on.filter((b) => b !== id) : d.bins.map((b) => b.id).filter((b) => b === id || on.includes(b));
		filters = { ...filters, [d.id]: next };
	};
</script>

<div class="bar">
	{#each DIMENSIONS as d (d.id)}
		<div class="dimension">
			<span class="label">{#if d.tip}<Term tip={d.tip}>{d.label}</Term>{:else}{d.label}{/if}</span>
			<div class="bins" role="group" aria-label={d.label}>
				{#each d.bins as b (b.id)}
					<button type="button" aria-pressed={filters[d.id].includes(b.id)} onclick={() => toggle(d, b.id)}>{b.label}</button>
				{/each}
			</div>
		</div>
	{/each}
	{#if anyFilters(filters)}
		<button type="button" class="clear" onclick={() => (filters = noFilters())}>Clear filters</button>
	{/if}
</div>

<style>
	.bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4em 1.2em; font-size: 0.82rem; }
	.dimension { display: flex; align-items: center; gap: 0.5em; }
	.label { color: var(--text-3); }
	.bins { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
	.bins button { font: inherit; padding: 0.15em 0.65em; border: 0; background: transparent; color: var(--text-2); cursor: pointer; }
	.bins button + button { border-left: 1px solid var(--border); }
	.bins button:hover { background: var(--surface-2); }
	.bins button[aria-pressed='true'] { background: var(--text); color: var(--surface); }
	.clear { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
</style>
