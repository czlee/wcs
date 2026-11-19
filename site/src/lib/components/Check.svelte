<script>
	// The final value of a metric as computed in this page, and whether it matches
	// the value scripts/compute_metrics.py computed (the one in the charts).
	import { TOLERANCE } from '#lib/metrics.js';
	import { fx } from '#lib/format.js';
	import Tex from './Tex.svelte';
	/** @type {{label: string, tex?: string, js: number, py: number}} */
	let { label, tex, js, py } = $props();
	const ok = $derived(Math.abs(js - py) <= TOLERANCE);
</script>

<p class="check">
	<strong>{#if tex}<Tex tex={`${tex} = ${fx(js)}`} />{:else}{label} = {fx(js)}{/if}</strong>
	{#if ok}
		<span class="ok" title="Python value: {py}">✓ matches the analysis (compute_metrics.py: {fx(py, 6)})</span>
	{:else}
		<span class="bad">✗ doesn’t match the analysis (compute_metrics.py: {py})</span>
	{/if}
</p>

<style>
	.check { margin: 0.6em 0; }
	.ok { color: var(--ok); font-size: 0.85rem; margin-left: 0.4em; }
	.bad { color: var(--bad); font-weight: 600; margin-left: 0.4em; }
</style>
