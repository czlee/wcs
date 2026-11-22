<script>
	// Where a percentile falls, on a track from least agreement (left) to most (right), in the
	// colours of the charts' agreement strip. Decorative: the number is always written beside it.
	/** @type {{pct: number}} */
	let { pct } = $props();
</script>

<span class="track" aria-hidden="true"><span class="mark" style:left="{pct}%"></span></span>

<style>
	.track {
		position: relative; display: inline-block; width: 7em; height: 6px; border-radius: 3px; vertical-align: middle;
		background: linear-gradient(to right, var(--bad), var(--grid), var(--ok));
	}
	.mark {
		position: absolute; top: -4px; bottom: -4px; width: 4px; margin-left: -2px; border-radius: 2px;
		background: var(--text); box-shadow: 0 0 0 1.5px var(--surface);
	}
</style>
