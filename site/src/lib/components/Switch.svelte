<script>
	// A segmented control: a row of buttons, exactly one pressed.
	/** @type {{options: {value: any, label: string}[], value: any, label: string}} */
	let { options, value = $bindable(), label } = $props();
</script>

<div class="switch" role="group" aria-label={label}>
	{#each options as o (o.value)}
		<button type="button" aria-pressed={value === o.value} onclick={() => (value = o.value)}>{o.label}</button>
	{/each}
</div>

<style>
	.switch { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; margin: 0.4em 0; vertical-align: middle; }
	button { font: inherit; font-size: 0.85rem; padding: 0.25em 0.9em; border: 0; background: transparent; color: var(--text-2); cursor: pointer; }
	button + button { border-left: 1px solid var(--border); }
	button[aria-pressed='true'] { background: var(--text); color: var(--surface); }
</style>
