<script>
	// Plain text in which [[metric_key|words]] is a link to that metric (see MetricLink).
	import MetricLink from './MetricLink.svelte';
	/** @type {{ text: string }} */
	let { text } = $props();
	const parts = $derived(
		text.split(/\[\[([a-z0-9_]+)\|([^\]]+)\]\]/).map((s, i) => ({ s, i }))
	);
</script>

{#each parts as { s, i } (i)}{#if i % 3 === 0}{s}{:else if i % 3 === 1}{@const label = parts[i + 1].s}<MetricLink k={s}>{label}</MetricLink>{/if}{/each}
