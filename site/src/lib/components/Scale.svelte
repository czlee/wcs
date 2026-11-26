<script>
	// A metric's values in numeric order, lowest on the left, with (where there is one) the value for random
	// ranking at `at` along the scale (the middle if that's not given). The colour runs red to green, or green
	// to red where `higher` is false: it fades through nothing in the middle, as the agreement colours
	// elsewhere do, rather than through yellow.
	/** @type {{ends: [import('#lib/about.js').End, import('#lib/about.js').End | null, import('#lib/about.js').End], higher: boolean}} */
	let { ends, higher } = $props();
	const [lo, mid, hi] = $derived(ends);
	const at = $derived(`${(mid?.at ?? 0.5) * 100}%`);
</script>

<div class="scale">
	<div class="words"><span>{lo.t}</span><span>{hi.t}</span></div>
	<div class="bar" class:flip={!higher}>
		<b class="lo">{lo.v}</b>
		{#if mid}<b class="mid" style:left={at}>{mid.v}</b>{/if}
		<b class="hi">{hi.v}</b>
	</div>
	{#if mid}<div class="under"><span style:left={at}>{mid.t}</span></div>{/if}
</div>

<style>
	.scale { margin: 0.6em auto 0.3em; max-width: 34em; }
	.words { display: flex; justify-content: space-between; gap: 0.5em; font-size: 0.9em; line-height: 1.25; color: var(--text-3); }
	.words span { max-width: 45%; }
	.words span:last-child { text-align: right; }
	.bar {
		position: relative; display: flex; justify-content: space-between; align-items: center;
		height: 1.7em; margin: 0.15em 0; padding: 0 0.6em; border-radius: 999px;
		--a: color-mix(in srgb, var(--bad) 55%, transparent); --b: color-mix(in srgb, var(--ok) 55%, transparent);
		background: linear-gradient(to right, var(--a), transparent, var(--b));
	}
	.bar.flip { background: linear-gradient(to right, var(--b), transparent, var(--a)); }
	.bar b { font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
	.bar .mid { position: absolute; transform: translateX(-50%); }
	.under { position: relative; height: 1.25em; font-size: 0.9em; line-height: 1.25; color: var(--text-3); }
	.under span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
</style>
