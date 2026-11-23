<script>
	// The final value of a metric as computed in this page, and whether it matches
	// the value scripts/compute_metrics.py computed (the one in the charts). A match
	// is a bare tick explained on hover; a mismatch is spelt out.
	import { TOLERANCE } from '#lib/metrics.js';
	import { fx } from '#lib/format.js';
	import Tex from './Tex.svelte';
	import Term from './Term.svelte';
	/** @type {{label: string, tex?: string, js: number, py: number, display?: boolean}} */
	let { label, tex, js, py, display = false } = $props();
	const ok = $derived(Math.abs(js - py) <= TOLERANCE);
	const tip = $derived(`Recalculated in your browser; matches the precomputed value used in the charts (${fx(py, 6)})`);
</script>

{#snippet verdict()}
	{#if ok}
		<span class="ok"><Term {tip} plain>✓</Term></span>
	{:else}
		<span class="bad">✗ doesn’t match the precomputed value used in the charts ({py})</span>
	{/if}
{/snippet}

{#if display && tex}
	<div class="check row">
		<Tex display tex={`${tex} = ${fx(js)}`} />
		{@render verdict()}
	</div>
{:else}
	<p class="check">
		<strong>{#if tex}<Tex tex={`${tex} = ${fx(js)}`} />{:else}{label} = {fx(js)}{/if}</strong>
		{@render verdict()}
	</p>
{/if}

<style>
	.check { margin: 0.6em 0; }
	/* The tick sits on the equation's text baseline (the line of the "="), not the middle of the box,
	   which a subscript under a Σ would pull down. A scroll container's baseline is its bottom edge, so
	   the scrolling is on the row instead of on the equation. */
	.row { display: flex; align-items: baseline; overflow-x: auto; overflow-y: hidden; }
	.check.row :global(.tex-display) { overflow: visible; flex: 0 0 auto; }
	.ok { color: var(--ok); margin-left: 0.3em; }
	.bad { color: var(--bad); font-weight: 600; margin-left: 0.4em; }
</style>
