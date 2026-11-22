<script>
	// A modal dialog (native <dialog>): Esc, the close button or a click on the
	// backdrop closes it. Its body renders only while it's open. `open` is bindable.
	// `heading`, where given, is drawn in place of the title (which still names the dialog).
	// When `view` changes, the dialog scrolls back to the top.
	/** @type {{open?: boolean, kicker?: string, title: string, wide?: boolean, view?: string, heading?: import('svelte').Snippet, children: import('svelte').Snippet}} */
	let { open = $bindable(false), kicker = '', title, wide = false, view, heading, children } = $props();
	/** @type {HTMLDialogElement | undefined} */
	let dialog = $state();
	/** @type {HTMLElement | undefined} */
	let body = $state();
	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) {
			dialog.showModal();
			// Not the first control, which might be a dropdown: the arrow keys should scroll.
			body?.focus({ preventScroll: true });
		} else if (!open && dialog.open) dialog.close();
	});
	$effect(() => {
		void view;
		dialog?.scrollTo(0, 0);
	});
	const onclick = (/** @type {MouseEvent} */ e) => {
		if (!dialog || e.target !== dialog) return;
		const b = dialog.getBoundingClientRect();
		if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) open = false;
	};
</script>

<dialog class:wide bind:this={dialog} onclose={() => (open = false)} {onclick} aria-label={title}>
	<header>
		<div class="titles">
			{#if kicker}<p class="kicker">{kicker}</p>{/if}
			<h2>{#if heading}{@render heading()}{:else}{title}{/if}</h2>
		</div>
		<button type="button" class="close" onclick={() => (open = false)} aria-label="Close">×</button>
	</header>
	<div class="body" tabindex="-1" bind:this={body}>
		{#if open}{@render children()}{/if}
	</div>
</dialog>

<style>
	dialog {
		width: min(760px, calc(100vw - 32px)); max-height: calc(100dvh - 48px); padding: 0;
		border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text);
		box-shadow: 0 8px 32px rgb(0 0 0 / 0.3);
	}
	dialog.wide { width: min(1100px, calc(100vw - 32px)); }
	dialog::backdrop { background: rgb(0 0 0 / 0.45); }
	header {
		position: sticky; top: 0; z-index: 1; display: flex; justify-content: space-between; align-items: start; gap: 1em;
		padding: 0.7em 1.1em 0.5em; background: var(--surface); border-bottom: 1px solid var(--border);
	}
	.kicker { margin: 0; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-3); }
	h2 { margin: 0.1em 0 0; font-size: 1.2rem; }
	.titles { flex: 1; min-width: 0; }
	.close {
		font: inherit; font-size: 1.6rem; line-height: 1; padding: 0 0.3em; border: 0; border-radius: 4px;
		background: transparent; color: var(--text-2); cursor: pointer;
	}
	.close:hover { background: var(--surface-2); color: var(--text); }
	.body { padding: 0.2em 1.1em 1.2em; outline: none; }
	@media (max-width: 860px) {
		dialog, dialog.wide { width: 100vw; max-width: 100vw; height: 100dvh; max-height: 100dvh; margin: 0; border: 0; border-radius: 0; }
	}
</style>
