<script>
	// Controls that narrow the scoresheets shown, one per dimension: a two-sided slider for
	// a range, otherwise toggle buttons (several bins can be on at once; none on means no
	// filter). `filters` is bindable.
	import { DIMENSIONS, anyFilters, noFilters, rangeChoice, rangeOf } from '#lib/dimensions.js';
	import Term from './Term.svelte';

	/** @type {{filters: import('#lib/dimensions.js').Filters}} */
	let { filters = $bindable() } = $props();

	const toggle = (/** @type {import('#lib/dimensions.js').Dimension} */ d, /** @type {string} */ id) => {
		const on = filters[d.id];
		// Kept in bin order, so the URL doesn't depend on the order of clicks.
		const next = on.includes(id) ? on.filter((b) => b !== id) : d.bins.map((b) => b.id).filter((b) => b === id || on.includes(b));
		filters = { ...filters, [d.id]: next };
	};

	// Move one end of a range, stopping at the other end.
	const slide = (/** @type {import('#lib/dimensions.js').Dimension} */ d, /** @type {'lo'|'hi'} */ end, /** @type {HTMLInputElement} */ input) => {
		const { lo, hi } = rangeOf(d, filters);
		const v = end === 'lo' ? Math.min(+input.value, hi) : Math.max(+input.value, lo);
		// The input may have moved past the stop without the state changing.
		input.value = String(v);
		filters = { ...filters, [d.id]: end === 'lo' ? rangeChoice(d, v, hi) : rangeChoice(d, lo, v) };
	};
	const stop = (/** @type {number} */ v, /** @type {number} */ max) => (v >= max ? `${max}+` : String(v));
</script>

<div class="bar">
	{#each DIMENSIONS as d (d.id)}
		<div class="dimension">
			<span class="label">{#if d.tip}<Term tip={d.tip}>{d.label}</Term>{:else}{d.label}{/if}</span>
			{#if d.range}
				{@const r = rangeOf(d, filters)}
				{@const frac = (/** @type {number} */ v) => (v - r.min) / (r.max - r.min)}
				<div class="slider" role="group" aria-label={d.label} style:--lo={frac(r.lo)} style:--hi={frac(r.hi)}>
					<span class="track"></span>
					<input class="lo" type="range" min={r.min} max={r.max} step="1" value={r.lo} autocomplete="off"
						aria-label="Fewest {d.label.toLowerCase()}" aria-valuetext={stop(r.lo, r.max)}
						oninput={(e) => slide(d, 'lo', e.currentTarget)} />
					<input class="hi" type="range" min={r.min} max={r.max} step="1" value={r.hi} autocomplete="off"
						aria-label="Most {d.label.toLowerCase()}" aria-valuetext={stop(r.hi, r.max)}
						oninput={(e) => slide(d, 'hi', e.currentTarget)} />
				</div>
				<output>{r.lo === r.hi || r.lo >= r.max ? stop(r.lo, r.max) : `${r.lo}–${stop(r.hi, r.max)}`}</output>
			{:else}
				<div class="bins" role="group" aria-label={d.label}>
					{#each d.bins as b (b.id)}
						<button type="button" aria-pressed={filters[d.id].includes(b.id)} onclick={() => toggle(d, b.id)}>{b.label}</button>
					{/each}
				</div>
			{/if}
		</div>
	{/each}
	{#if anyFilters(filters)}
		<button type="button" class="clear" onclick={() => (filters = noFilters())}>Clear filters</button>
	{/if}
</div>

<style>
	.bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4em 0.9em; font-size: 0.82rem; }
	.dimension { display: flex; align-items: center; gap: 0.5em; }
	.label { color: var(--text-3); }
	.bins { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
	.bins button { font: inherit; padding: 0.15em 0.5em; border: 0; background: transparent; color: var(--text-2); cursor: pointer; }
	.bins button + button { border-left: 1px solid var(--border); }
	.bins button:hover { background: var(--surface-2); }
	.bins button[aria-pressed='true'] { background: var(--text); color: var(--surface); }
	/* Two native sliders on one track, each shifted by a thumb's width, so that the handles
	   sit side by side (and both can be grabbed) when they're at the same value. */
	.slider { --thumb: 14px; --span: calc(100% - 2 * var(--thumb)); position: relative; width: 13em; height: 20px; }
	.track, .track::after { position: absolute; top: 50%; height: 4px; margin-top: -2px; border-radius: 2px; }
	.track { left: 0; right: 0; background: var(--border); }
	.track::after {
		content: ''; top: 0; margin-top: 0; background: var(--accent);
		left: calc(var(--thumb) / 2 + var(--lo) * var(--span));
		right: calc(var(--thumb) / 2 + (1 - var(--hi)) * var(--span));
	}
	.slider input {
		position: absolute; top: 0; height: 100%; width: calc(100% - var(--thumb)); margin: 0;
		appearance: none; background: none; pointer-events: none;
	}
	.slider .lo { left: 0; }
	.slider .hi { right: 0; }
	.slider input::-webkit-slider-runnable-track { background: none; }
	.slider input::-moz-range-track { background: none; }
	.slider input::-webkit-slider-thumb {
		appearance: none; box-sizing: border-box; width: var(--thumb); height: 18px; border-radius: 4px;
		border: 2px solid var(--surface); background: var(--accent); pointer-events: auto; cursor: ew-resize;
	}
	.slider input::-moz-range-thumb {
		box-sizing: border-box; width: var(--thumb); height: 18px; border-radius: 4px;
		border: 2px solid var(--surface); background: var(--accent); pointer-events: auto; cursor: ew-resize;
	}
	.slider input:focus-visible { outline: none; }
	.slider input:focus-visible::-webkit-slider-thumb { outline: 2px solid var(--text); }
	.slider input:focus-visible::-moz-range-thumb { outline: 2px solid var(--text); }
	/* Fixed width, so the controls beside it don't shift as it changes. */
	output { min-width: 3.4em; color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
	.clear { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
</style>
