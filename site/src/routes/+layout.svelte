<script>
	// Manrope, self-hosted via Fontsource (SIL Open Font License); latin and latin-ext subsets.
	import '@fontsource/manrope/400.css';
	import '@fontsource/manrope/600.css';
	import '@fontsource/manrope/700.css';
	import 'katex/dist/katex.min.css';
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { DRAFT } from '#lib/config.js';
	import { explorer } from '#lib/explorer.js';
	import { link, date } from '#lib/format.js';
	import { FORMATS } from '#lib/levels.js';
	import { page } from '$app/state';

	// Strictly pages take the Strictly colour as their accent, so everything that reads --accent follows.
	const strictly = $derived(page.data.format === 'strictly');

	/** @type {{children: import('svelte').Snippet, data: any}} */
	let { children, data } = $props();
	const limitationsHref = $derived(`${link(FORMATS[strictly ? 'strictly' : 'jnj'].path)}?dialog=limitations`);
	// The limitations open over what's on show.
	function openLimitations(/** @type {MouseEvent} */ e) {
		if (!explorer.open || e.button || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
		e.preventDefault();
		explorer.open('limitations');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/svg+xml" />
	{#if DRAFT}<meta name="robots" content="noindex, nofollow" />{/if}
</svelte:head>

<div class="shell">
{#if DRAFT}
	<div class="draft-banner" role="note">
		<strong>DRAFT</strong> · Work in progress: numbers, wording and layout may change.
	</div>
{/if}

<main class:strictly>
	{@render children()}
</main>

<footer>
	<p>
		Analysis by Chuan-Zheng Lee. Exploratory, not adjusted for panel or field size; see the
		<a href={limitationsHref} onclick={openLimitations}>limitations</a>. This site doesn’t rate individual judges.
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
	.draft-banner {
		background: #fab219; color: #1a1a19; font-size: 0.85rem; text-align: center; padding: 0.35em 16px;
	}
	main { padding: 0 16px 3em; }
	footer { border-top: 1px solid var(--border); color: var(--text-3); font-size: 0.72rem; padding: 0.3em 16px 0.4em; }
	footer p { margin: 0.15em 0; max-width: none; }
	footer a { color: var(--text-2); }
	/* On a large screen the explorer is an app: the window, with no page scroll. */
	@media (min-width: 900px) and (min-height: 600px) {
		.shell { height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }
		main { flex: 1; min-height: 0; padding-bottom: 0; }
	}
</style>
