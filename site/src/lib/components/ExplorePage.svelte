<script>
	// The explorer: one metric at a time for one dance format. On a large screen it's
	// an app that fills the window: a top bar, a metric rail, then the metric's bar
	// chart and box plot filling the space, with what it measures and its caveats
	// underneath. The intro, the limitations and the working are dialogs. The metric
	// is in the URL (?metric=…); without one, a random metric that isn't `hidden` is
	// picked on load. Smaller screens get a plain scrolling page for now.
	import { onMount } from 'svelte';
	import Limitations from './Limitations.svelte';
	import MetricChart from './MetricChart.svelte';
	import Modal from './Modal.svelte';
	import WorkedConcordance from './WorkedConcordance.svelte';
	import WorkedOrder from './WorkedOrder.svelte';
	import WorkedTop from './WorkedTop.svelte';
	import WorkedSpread from './WorkedSpread.svelte';
	import { FAMILIES, FAMILY_OF, METRICS, METRIC_KEYS } from '#lib/families.js';
	import { ABOUT } from '#lib/about.js';
	import { FORMATS } from '#lib/levels.js';
	import { DRAFT } from '#lib/config.js';
	import { link, date } from '#lib/format.js';

	let { data } = $props();
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (data.format)]);
	const other = $derived(Object.values(FORMATS).find((f) => f.id !== data.format));
	const rows = $derived(data.rows);
	const WORKED = { concordance: WorkedConcordance, order: WorkedOrder, top: WorkedTop, spread: WorkedSpread };
	/** Matches the layout's app-mode media query (src/routes/+layout.svelte). */
	const APP_QUERY = '(min-width: 900px) and (min-height: 600px)';

	// Metrics in picker order (family by family), and those a random pick can land on.
	const ORDER = FAMILIES.flatMap((f) => f.metrics);
	const PICKABLE = ORDER.filter((k) => !METRICS[k].hidden);

	// Until the page loads in a browser (or without JavaScript), the first metric.
	let key = $state(PICKABLE[0]);
	const meta = $derived(METRICS[key]);
	const family = $derived(FAMILY_OF[key]);
	const about = $derived(ABOUT[key]);
	const Worked = $derived(WORKED[/** @type {keyof typeof WORKED} */ (family.id)]);

	const randomMetric = () => {
		const others = PICKABLE.filter((k) => k !== key);
		key = others[Math.floor(Math.random() * others.length)];
	};
	const step = (/** @type {number} */ d) => (key = ORDER[(ORDER.indexOf(key) + d + ORDER.length) % ORDER.length]);

	let workedOpen = $state(false);
	let aboutOpen = $state(false);
	let limitsOpen = $state(false);
	const INTRO_SEEN = 'wcs-explore-intro-seen';

	let mounted = $state(false);
	let app = $state(false);
	onMount(() => {
		const k = new URLSearchParams(location.search).get('metric');
		if (k && k in METRICS) key = k;
		else key = PICKABLE[Math.floor(Math.random() * PICKABLE.length)];
		mounted = true;
		pickRandomSheet();
		// The intro opens by itself on a first visit only.
		try {
			if (!localStorage.getItem(INTRO_SEEN)) { aboutOpen = true; localStorage.setItem(INTRO_SEEN, '1'); }
		} catch { /* storage blocked: skip the intro */ }
		const mq = matchMedia(APP_QUERY);
		const sync = () => (app = mq.matches);
		sync();
		mq.addEventListener('change', sync);
		return () => mq.removeEventListener('change', sync);
	});
	// Keep the URL in step, so a reload or a shared link shows the same metric.
	$effect(() => {
		if (!mounted) return;
		const p = new URLSearchParams(location.search);
		p.set('metric', key);
		history.replaceState(history.state, '', `?${p}`);
	});

	// ← and → step through the metrics, unless a dialog is open or the reader is typing.
	const onKey = (/** @type {KeyboardEvent} */ e) => {
		if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
		if (workedOpen || aboutOpen || limitsOpen) return;
		if (/** @type {HTMLElement} */ (e.target).closest('input, select, textarea')) return;
		if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
		else if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
	};

	// The scoresheet "How is this calculated?" works through: one chosen at random on load
	// (the fallback until it arrives), or the one whose point was clicked in the box plot.
	let sheet = $derived(/** @type {import('#lib/server/data.js').Sheet} */ (data.fallback));
	let clicked = $state(false);
	let loading = $state(false);
	async function loadSheet(/** @type {string} */ id) {
		loading = true;
		try {
			const res = await fetch(link(`/sheet/${id}/data.json`));
			if (res.ok) { sheet = await res.json(); return true; }
			return false;
		} finally {
			loading = false;
		}
	}
	async function pickRandomSheet() {
		const ids = rows.map((/** @type {any} */ r) => r.id).filter((/** @type {string} */ id) => id !== sheet.id);
		if (await loadSheet(ids[Math.floor(Math.random() * ids.length)])) clicked = false;
	}
	// A click on a point in the box plot shows that scoresheet's calculation.
	async function showSheet(/** @type {string} */ id) {
		if (id !== sheet.id && !(await loadSheet(id))) return;
		clicked = true;
		workedOpen = true;
	}
	const sheetCharted = $derived(sheet.competitors.length >= (meta.minN ?? 0));
</script>

<svelte:window onkeydown={onKey} />

<div class="explorer" class:app>
	<header class="topbar">
		<a class="brand" href={link('/')}>WCS judge divergence{#if DRAFT}<span class="draft-tag">DRAFT</span>{/if}</a>
		<div class="formats" role="group" aria-label="Dance format">
			{#each Object.values(FORMATS) as f (f.id)}
				<a href="{link(f.path)}?metric={key}" aria-current={f.id === data.format ? 'page' : undefined}
					style:--c={f.colour}>{f.label}</a>
			{/each}
		</div>
		<span class="count small muted">{rows.length} finals, {date(data.info.first_event)} to {date(data.info.last_event)}</span>
		<span class="spacer"></span>
		<button type="button" class="warn" onclick={() => (limitsOpen = true)}>⚠ Exploratory: read the limitations</button>
		<button type="button" class="link-btn" onclick={() => (aboutOpen = true)}>About</button>
		<a class="small" href={link(fmt.longPath)}>Long-form page</a>
		<a class="small" href={link('/sheets/')}>All scoresheets</a>
	</header>

	<div class="body">
		<nav class="rail" aria-label="Metrics">
			<label class="select">
				<span class="small muted">Metric</span>
				<select bind:value={key}>
					{#each FAMILIES as f (f.id)}
						<optgroup label={f.title}>
							{#each f.metrics as k (k)}<option value={k}>{METRICS[k].label}</option>{/each}
						</optgroup>
					{/each}
				</select>
			</label>
			<div class="list">
				{#each FAMILIES as f (f.id)}
					<div class="fam">
						<div class="fam-title">{f.title}</div>
						{#each f.metrics as k (k)}
							<button type="button" class:hidden-metric={METRICS[k].hidden} aria-pressed={k === key} onclick={() => (key = k)}>
								{METRICS[k].label}
							</button>
						{/each}
					</div>
				{/each}
			</div>
		</nav>

		<section class="view">
			<div class="head">
				<div>
					<p class="kicker">{family.title}</p>
					<h1 class="metric">{meta.label}</h1>
					<p class="direction small">
						<span class="dot" class:ok={meta.higher} class:bad={!meta.higher}></span>
						{meta.higher ? 'Higher' : 'Lower'} means more agreement{#if meta.minN}{' · '}finals of {meta.minN} or more competitors{/if}
					</p>
				</div>
				<div class="controls">
					<button type="button" class="btn" onclick={() => step(-1)} aria-label="Previous metric" title="Previous metric (←)">←</button>
					<button type="button" class="btn" onclick={() => step(1)} aria-label="Next metric" title="Next metric (→)">→</button>
					<button type="button" class="btn" onclick={randomMetric}>Random metric</button>
					<button type="button" class="btn primary" onclick={() => (workedOpen = true)}>How is this calculated?</button>
				</div>
			</div>

			<div class="charts">
				{#key key}
					<MetricChart {rows} index={METRIC_KEYS.indexOf(key)} {meta} colour={fmt.colour} format={data.format} fill={app}
						highlight={mounted && sheetCharted ? sheet.id : undefined} onpoint={showSheet} />
				{/key}
			</div>

			<div class="panels">
				<div class="panel">
					<h2>What it measures</h2>
					<p>{about.what}</p>
					<p>{about.reading}</p>
				</div>
				<div class="panel">
					<h2>Caveats for this metric</h2>
					{#if about.caveats.length}
						<ul>{#each about.caveats as c, i (i)}<li>{c}</li>{/each}</ul>
					{/if}
					<p class="small muted">
						{about.caveats.length ? 'Also see the' : 'See the'}
						<button type="button" class="link-btn" onclick={() => (limitsOpen = true)}>limitations</button>
						that apply to every metric: panel and field sizes differ between levels, scoresheets aren’t
						independent, and more.
					</p>
				</div>
			</div>
		</section>
	</div>
</div>

<Modal bind:open={workedOpen} kicker="How is this calculated?" title={meta.label} wide>
	<p class="sheet">
		<strong>{sheet.name}</strong> ({date(sheet.date)}){#if mounted && sheetCharted}, ringed in the box plot{/if}
	</p>
	<p class="sheet-links small">
		{clicked ? 'The scoresheet you clicked.' : 'A scoresheet chosen at random.'} To see another, close this and click its
		point in the box plot, or
		<button class="link-btn" onclick={pickRandomSheet} disabled={loading}>{loading ? 'loading…' : 'pick one at random'}</button>. ·
		<a href={link(`/sheet/${sheet.id}/`)}>All metrics for this scoresheet</a>
	</p>
	{#key `${sheet.id}/${key}`}<Worked {sheet} focus={key} />{/key}
</Modal>

<Modal bind:open={limitsOpen} kicker="Before you read anything into this" title="Reasons these comparisons might mislead">
	<Limitations info={data.info} bare />
</Modal>

<Modal bind:open={aboutOpen} kicker="About" title="How much do WCS judges disagree?">
	<p class="byline">By Chuan-Zheng Lee<span class="credit">, with implementation by Claude</span></p>
	<p>
		In a West Coast Swing final, every judge ranks every competitor, and relative placement combines those
		rankings into the result. This looks at the rankings before they’re combined: how different are the
		judges’ rankings from each other, and does that vary by division level? It covers
		<strong>{rows.length} {fmt.label} finals</strong> from {date(data.info.first_event)} to
		{date(data.info.last_event)}.{#if other}
			{' '}<a href="{link(other.path)}?metric={key}">{other.label} finals</a> are a click away in the top bar.{/if}
	</p>
	<p>
		There are many ways to measure how far apart rankings are, and they don’t all answer the same question.
		This uses twelve, in four families. Pick one on the left (or step through them with ← and →); the bar
		chart shows its mean by level, and the box plot shows every final.
	</p>
	<p>
		Every number can be checked. Each scoresheet links to its published source, and “How is this
		calculated?” recalculates the metric in your browser, step by step, and checks the result against the
		analysis. Click a point in the box plot for that scoresheet’s working, or a bar to list its finals.
	</p>
	<p class="callout small">
		<strong>This is exploratory.</strong> Panel and field sizes differ between levels, and most of these
		metrics depend on them. <button type="button" class="link-btn" onclick={() => { aboutOpen = false; limitsOpen = true; }}>Read the limitations</button>
		before reading anything into a difference.
	</p>
	<p><button type="button" class="btn primary" onclick={() => (aboutOpen = false)}>Start exploring</button></p>
</Modal>

<style>
	/* ---- Shared (both the app and the scrolling fallback) ---- */
	.topbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4em 1em; padding: 0.55em 0; border-bottom: 1px solid var(--border); }
	.brand { color: var(--text); font-weight: 700; text-decoration: none; }
	.draft-tag {
		font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; vertical-align: 0.2em; margin-left: 0.5em;
		padding: 0.1em 0.4em; border-radius: 3px; background: #fab219; color: #1a1a19;
	}
	.spacer { flex: 1; }
	.topbar a.small { color: var(--text-2); }
	.formats { display: flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
	.formats a { text-align: center; padding: 0.2em 0.8em; font-size: 0.86rem; text-decoration: none; color: var(--text-2); }
	.formats a + a { border-left: 1px solid var(--border); }
	.formats a[aria-current='page'] { background: var(--c); color: #fff; font-weight: 600; }
	.warn {
		font: inherit; font-size: 0.82rem; cursor: pointer; padding: 0.2em 0.7em; border-radius: 4px;
		border: 1px solid var(--warn-border); background: var(--warn-bg); color: var(--warn-text);
	}
	.link-btn { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
	.topbar .link-btn { font-size: 0.85rem; color: var(--text-2); }

	.body { display: grid; grid-template-columns: 12em minmax(0, 1fr); gap: 1.4em; margin-top: 1em; }
	.select { display: none; }
	.select select { font: inherit; width: 100%; padding: 0.3em; margin-top: 0.2em; }
	.list { display: flex; flex-direction: column; gap: 0.7em; }
	.fam-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-3); margin-bottom: 0.15em; }
	.list button {
		display: block; width: 100%; text-align: left; font: inherit; font-size: 0.82rem; line-height: 1.3;
		padding: 0.25em 0.45em; border: 0; border-left: 3px solid transparent; border-radius: 0 4px 4px 0;
		background: transparent; color: var(--text-2); cursor: pointer;
	}
	.list button:hover { background: var(--surface-2); color: var(--text); }
	.list button[aria-pressed='true'] { border-left-color: var(--accent); background: var(--surface-2); color: var(--text); font-weight: 600; }
	.list button.hidden-metric { font-style: italic; }

	.view { min-width: 0; }
	.head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: end; gap: 0.6em 1.5em; margin-bottom: 0.6em; }
	.kicker { margin: 0; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-3); }
	h1.metric { margin: 0.05em 0 0.1em; font-size: 1.5rem; }
	.direction { margin: 0; color: var(--text-2); }
	.dot { display: inline-block; width: 0.6em; height: 0.6em; border-radius: 50%; margin-right: 0.2em; }
	.dot.ok { background: var(--ok); }
	.dot.bad { background: var(--bad); }
	.controls { display: flex; flex-wrap: wrap; gap: 0.4em; }
	.btn.primary { font-weight: 600; border-color: var(--accent); color: var(--accent); }

	.panels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8em; margin-top: 0.8em; }
	.panel { border: 1px solid var(--border); border-radius: 6px; padding: 0.35em 0.8em 0.4em; font-size: 0.82rem; line-height: 1.45; }
	.panel h2 { margin: 0.15em 0 0.25em; font-size: 0.85rem; }
	.panel p, .panel li { margin: 0.3em 0; max-width: none; }
	.panel .small { font-size: 0.78rem; }
	.panel ul { margin: 0.25em 0; padding-left: 1.2em; }
	.panel li + li { margin-top: 0.2em; }

	.sheet { margin-bottom: 0.1em; }
	.sheet-links { margin-top: 0; color: var(--text-2); }
	.byline { margin-top: 0.2em; color: var(--text-2); font-size: 0.9rem; }
	.byline .credit { color: var(--text-3); }

	/* ---- The app: the explorer fills the main area and nothing scrolls but the info panels ---- */
	.explorer.app { height: 100%; display: flex; flex-direction: column; }
	.app .body { flex: 1; min-height: 0; margin-top: 0.8em; }
	.app .rail { overflow-y: auto; min-height: 0; padding-bottom: 0.8em; }
	.app .view { display: flex; flex-direction: column; min-height: 0; }
	.app .charts { flex: 1; min-height: 240px; }
	.app .panels { flex: none; max-height: 11em; padding-bottom: 0.6em; }
	.app .panel { overflow-y: auto; }

	/* ---- Narrow screens (to be redesigned): a scrolling page with a dropdown ---- */
	@media (max-width: 860px) {
		.body { grid-template-columns: minmax(0, 1fr); gap: 1em; }
		.list { display: none; }
		.select { display: block; }
		.panels { grid-template-columns: minmax(0, 1fr); }
		.count { display: none; }
	}
</style>
