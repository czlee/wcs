<script>
	// DM Sans, self-hosted via Fontsource (SIL Open Font License); latin and latin-ext subsets.
	import '@fontsource/dm-sans/400.css';
	import '@fontsource/dm-sans/600.css';
	import '@fontsource/dm-sans/700.css';
	import 'katex/dist/katex.min.css';
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import { DRAFT } from '#lib/config.js';
	import { link, date } from '#lib/format.js';
	import { page } from '$app/state';

	/** @type {{children: import('svelte').Snippet, data: any}} */
	let { children, data } = $props();
	const nav = [
		{ href: '/', route: '/', label: 'Jack & Jill' },
		{ href: '/strictly/', route: '/strictly', label: 'Strictly' },
		{ href: '/sheets/', route: '/sheets', label: 'All scoresheets' }
	];
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/svg+xml" />
	{#if DRAFT}<meta name="robots" content="noindex, nofollow" />{/if}
</svelte:head>

{#if DRAFT}
	<div class="draft-banner" role="note">
		<strong>DRAFT</strong> · Work in progress: numbers, wording and layout may change.
	</div>
{/if}

<header>
	<nav>
		<a class="brand" href={link('/')}>WCS judge divergence{#if DRAFT}<span class="draft-tag">DRAFT</span>{/if}</a>
		{#each nav as item (item.href)}
			<a href={link(item.href)} aria-current={page.route.id === item.route ? 'page' : undefined}>{item.label}</a>
		{/each}
	</nav>
</header>

<main>
	{@render children()}
</main>

<footer>
	<p>
		Analysis by Chuan-Zheng Lee. Exploratory, not adjusted for panel or field size; see the
		<a href={link('/#limitations')}>limitations</a>. This site doesn’t rate individual judges.
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
	footer { border-top: 1px solid var(--border); color: var(--text-3); font-size: 0.8rem; padding-block: 1em 2em; }
	footer a { color: var(--text-2); }
</style>
