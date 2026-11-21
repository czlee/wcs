<script>
	// A term with a definition that shows on hover, keyboard focus, or tap. The tooltip
	// is kept inside the viewport and drops below the term if there's no room above.
	// It's position: fixed, so a scrolling ancestor (e.g. .table-wrap) can't clip it;
	// that's safe because it closes on scroll. `plain` drops the dotted underline.
	/** @type {{ tip: string, plain?: boolean, children: import('svelte').Snippet }} */
	let { tip, plain = false, children } = $props();
	const id = $props.id();
	let open = $state(false);
	/** @type {HTMLButtonElement | undefined} */
	let trigger = $state();
	/** @type {HTMLSpanElement | undefined} */
	let box = $state();
	let left = $state(0);
	let top = $state(0);

	$effect(() => {
		if (!open || !trigger || !box) return;
		const t = trigger.getBoundingClientRect();
		const w = box.offsetWidth;
		const h = box.offsetHeight;
		const margin = 8;
		left = Math.min(Math.max(t.left + t.width / 2 - w / 2, margin), innerWidth - margin - w);
		top = t.top < h + 12 ? t.bottom + 6 : t.top - h - 6;

		const close = (/** @type {Event} */ ev) => {
			if (ev instanceof KeyboardEvent ? ev.key === 'Escape' : !trigger?.contains(/** @type {Node} */ (ev.target)))
				open = false;
		};
		addEventListener('pointerdown', close);
		addEventListener('keydown', close);
		// Capture, so scrolling any container (the modal, a .table-wrap) closes it too: scroll doesn't bubble.
		addEventListener('scroll', close, { capture: true, passive: true });
		return () => {
			removeEventListener('pointerdown', close);
			removeEventListener('keydown', close);
			removeEventListener('scroll', close, { capture: true });
		};
	});
</script>

<span class="wrap"><button
		type="button"
		class="term"
		class:plain
		aria-describedby={id}
		bind:this={trigger}
		onclick={() => (open = true)}
		onmouseenter={() => (open = true)}
		onmouseleave={() => (open = false)}
		onfocus={() => (open = true)}
		onblur={() => (open = false)}>{@render children()}</button><span
		{id}
		role="tooltip"
		class="tip"
		class:open
		bind:this={box}
		style:left="{left}px"
		style:top="{top}px">{tip}</span></span>

<style>
	.term {
		font: inherit; color: inherit; background: none; border: 0; padding: 0; margin: 0;
		text-decoration: underline dotted; text-underline-offset: 0.2em; cursor: help;
	}
	.term.plain { text-decoration: none; }
	.tip {
		/* display: none when closed, so the hidden box can't widen the page on phones. */
		display: none; position: fixed; z-index: 10;
		width: max-content; max-width: min(18em, calc(100vw - 16px)); padding: 0.45em 0.65em;
		border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text);
		font-size: 0.85rem; font-weight: 400; line-height: 1.35; text-align: left; white-space: normal;
		box-shadow: 0 2px 8px rgb(0 0 0 / 0.15);
	}
	.tip.open { display: block; }
</style>
