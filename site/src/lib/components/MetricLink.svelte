<script>
	// A mention of another metric in prose, as a link that makes it the current metric: the chart on the
	// main page, the working in the calculation dialog. The explorer supplies what that does.
	import { getContext } from 'svelte';
	/** @type {{ k: string, children: import('svelte').Snippet }} */
	let { k, children } = $props();
	const show = getContext('showMetric');
</script>

<button type="button" class="metric-link" onclick={() => show?.(k)}>{@render children()}</button>

<style>
	.metric-link { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
</style>
