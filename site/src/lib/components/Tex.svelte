<script>
	// A TeX expression typeset with KaTeX. It renders to plain HTML, so it works in
	// the prerendered page and re-renders in the browser when its numbers change.
	import katex from 'katex';
	/** @type {{tex: string, display?: boolean}} */
	let { tex, display = false } = $props();
	const html = $derived(katex.renderToString(tex, { displayMode: display, throwOnError: false, strict: false, output: 'html' }));
</script>

{#if display}
	<div class="tex-display">{@html html}</div>
{:else}
	<span class="tex-inline">{@html html}</span>
{/if}

<style>
	/* Long substituted formulas scroll on narrow screens instead of widening the page. */
	.tex-display { overflow-x: auto; overflow-y: hidden; padding: 0.1em 0 0.2em 1em; }
	.tex-display :global(.katex-display) { margin: 0.4em 0; text-align: left; }
	.tex-display :global(.katex-display > .katex) { text-align: left; }
	.tex-inline { white-space: nowrap; }
	:global(.katex) { font-size: 1.08em; }
</style>
