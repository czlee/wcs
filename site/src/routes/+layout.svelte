<script>
	// Manrope, self-hosted via Fontsource (SIL Open Font License); latin and latin-ext subsets.
	import '@fontsource/manrope/400.css';
	import '@fontsource/manrope/600.css';
	import '@fontsource/manrope/700.css';
	import 'katex/dist/katex.min.css';
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { DRAFT } from '#lib/config.js';
	import { link, date } from '#lib/format.js';
	import { page } from '$app/state';

	// Strictly pages take the Strictly colour as their accent, so everything that reads --accent follows.
	const strictly = $derived((page.data.sheet?.format ?? page.data.format) === 'strictly');
	// The explorer draws its own top bar in place of the nav and, on a large screen, fills the window.
	const explore = $derived(!!page.data.explorer);

	/** @type {{children: import('svelte').Snippet, data: any}} */
	let { children, data } = $props();
	const nav = [
		{ href: '/', routes: ['/', '/strictly'], label: 'Explore' },
		{ href: '/long-form/', routes: ['/long-form', '/long-form/strictly'], label: 'Long-form' },
		{ href: '/sheets/', routes: ['/sheets'], label: 'All scoresheets' }
	];
	const current = (/** @type {string[]} */ routes) => routes.includes(page.route.id ?? '');
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/svg+xml" />
	{#if DRAFT}<meta name="robots" content="noindex, nofollow" />{/if}
</svelte:head>

<div class="shell" class:explore>
{#if DRAFT}
	<div class="draft-banner" role="note">
		<strong>DRAFT</strong> · Work in progress: numbers, wording and layout may change.
	</div>
{/if}

{#if !explore}
<header>
	<nav>
		<a class="brand" href={link('/')}>WCS judge divergence{#if DRAFT}<span class="draft-tag">DRAFT</span>{/if}</a>
		{#each nav as item (item.href)}
			<a href={link(item.href)} aria-current={current(item.routes) ? 'page' : undefined}>{item.label}</a>
		{/each}
	</nav>
</header>
{/if}

<main class:strictly class:wide={explore}>
	{@render children()}
</main>

<footer>
	<p>
		Analysis by Chuan-Zheng Lee. Exploratory, not adjusted for panel or field size; see the
		<a href={link('/long-form/#limitations')}>limitations</a>. This site doesn’t rate individual judges.
	</p>
	<p>
		The method and design decisions are mine; the code, including the data processing and this
		website, was largely written by <a href="https://claude.ai/">Claude</a>, under my direction.
	</p>
	<p>
		Data: published finals scoresheets from <a href="https://scoring.dance/">scoring.dance</a>,
		<a href="https://eepro.com/">eepro.com</a> and <a href="https://danceconvention.net/">danceconvention.net</a>,
		events {date(data.info.first_event)} to {date(data.info.last_event)}; {data.info.sheets} scoresheets,
		exported {date(data.info.exported)} from commit <code>{data.info.commit}</code>. Code:
		<a href="https://github.com/czlee/wcs">czlee/wcs</a>.
	</p>
</footer>
</div>

<style>
	header { border-bottom: 1px solid var(--border); }
	.draft-banner {
		background: #fab219; color: #1a1a19; font-size: 0.85rem; text-align: center; padding: 0.35em 16px;
	}
	.draft-tag {
		font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; vertical-align: 0.2em; margin-left: 0.5em;
		padding: 0.1em 0.4em; border-radius: 3px; background: #fab219; color: #1a1a19;
	}
	nav, main, footer { max-width: 1040px; margin: 0 auto; padding: 0 16px; }
	nav { display: flex; flex-wrap: wrap; gap: 0.3em 1.2em; align-items: baseline; padding-block: 0.7em; }
	nav a { color: var(--text-2); text-decoration: none; }
	nav a[aria-current='page'] { color: var(--text); font-weight: 600; }
	nav .brand { color: var(--text); font-weight: 700; margin-right: auto; }
	main { padding-bottom: 3em; }
	/* The explorer uses the full width for its charts (prose inside keeps its own measure). */
	main.wide { max-width: none; }
	.explore footer { font-size: 0.72rem; padding-block: 0.3em 0.4em; }
	.explore footer p { margin: 0.15em 0; }
	/* On a large screen the explorer is an app: the window, with no page scroll. */
	@media (min-width: 900px) and (min-height: 600px) {
		.shell.explore { height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }
		/* Auto side margins would shrink flex items to their content: stretch them instead. */
		.shell.explore > :global(*) { width: 100%; margin-inline: 0; }
		.explore main { flex: 1; min-height: 0; padding-bottom: 0; }
	}
	/* The footer runs the full width on every page, which keeps it to a few lines. */
	footer { max-width: none; border-top: 1px solid var(--border); color: var(--text-3); font-size: 0.75rem; padding-block: 0.5em 0.8em; }
	footer p { margin: 0.25em 0; max-width: none; }
	footer a { color: var(--text-2); }
</style>
