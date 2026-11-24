<script>
	// The explorer: one metric at a time for one dance format. On a large screen it's
	// an app that fills the window: a top bar, a metric rail, then the metric's bar
	// chart and box plot filling the space, with what it measures and its caveats
	// underneath. The intro, the limitations, the working and a scoresheet's profile are
	// dialogs, which can lead to each other: one is open at a time. What's
	// on show, dialogs included, is in the URL (see lib/view.js); without a metric there, a random
	// one that isn't `hidden` is picked on load. Smaller screens get a plain scrolling page for now.
	import { onMount, setContext } from 'svelte';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import Linked from './Linked.svelte';
	import Limitations from './Limitations.svelte';
	import FilterBar from './FilterBar.svelte';
	import MetricChart from './MetricChart.svelte';
	import Modal from './Modal.svelte';
	import MetricsTable from './MetricsTable.svelte';
	import RankMatrix from './RankMatrix.svelte';
	import SheetMeta from './SheetMeta.svelte';
	import SheetPicker from './SheetPicker.svelte';
	import Standing from './Standing.svelte';
	import WorkedSquared from './WorkedSquared.svelte';
	import WorkedHeadToHead from './WorkedHeadToHead.svelte';
	import WorkedTop from './WorkedTop.svelte';
	import WorkedGaps from './WorkedGaps.svelte';
	import { FAMILIES, FAMILY_OF, METRICS, METRIC_KEYS } from '#lib/families.js';
	import { anyFilters, matches, noFilters, queryString, setFilterParams } from '#lib/dimensions.js';
	import { ABOUT } from '#lib/about.js';
	import { FORMATS } from '#lib/levels.js';
	import { DRAFT } from '#lib/config.js';
	import { explorer } from '#lib/explorer.js';
	import { aboutSheet, parseView, viewQuery } from '#lib/view.js';
	import { link, date } from '#lib/format.js';

	let { data } = $props();
	const fmt = $derived(FORMATS[/** @type {'jnj'|'strictly'} */ (data.format)]);
	const other = $derived(Object.values(FORMATS).find((f) => f.id !== data.format));
	const rows = $derived(data.rows);
	const WORKED = { l2: WorkedSquared, l1: WorkedGaps, 'head-to-head': WorkedHeadToHead, top: WorkedTop };
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

	let filters = $state.raw(noFilters());
	const filtered = $derived(rows.filter((/** @type {any} */ r) => matches(r, filters)));
	/** The metric and filters as a query string, for links to the other format. */
	const query = $derived(queryString(setFilterParams(new URLSearchParams({ metric: key }), filters)));

	const step = (/** @type {number} */ d) => (key = ORDER[(ORDER.indexOf(key) + d + ORDER.length) % ORDER.length]);

	const INTRO_SEEN = 'wcs-explore-intro-seen';

	// What's on show is also in the URL (see lib/view.js), so that it survives a reload, can be
	// shared, and Back and Forward move through it. Opening a dialog adds a history entry; any
	// other change rewrites the current one. `page.state.depth` is how many entries back the
	// explorer without a dialog is.
	let dialog = $state(/** @type {import('#lib/view.js').Dialog | null} */ (null));
	/** Whether the open dialog is the intro shown by itself on a first visit, which isn't in the URL. */
	let intro = $state(false);
	/** Whether the URL names the scoresheet: once it's chosen, or a dialog about it is opened. */
	let pinned = $state(false);
	/** Whether the URL has yet to be shown in full, so that it mustn't be rewritten. */
	let showing = $state(true);
	/** Whether the dialog was closed, and the browser is on its way back to the entry without it. */
	let closing = $state(false);
	const home = $derived(link(fmt.path));
	const viewUrl = () => home + viewQuery(
		{ metric: key, filters, sheet: pinned ? sheet.id : null, dialog: intro ? null : dialog }, location.search);

	/** @type {ReturnType<typeof setTimeout> | undefined} */
	let timer;
	let writes = Promise.resolve();
	/** Write the view into the URL, in a new history entry if `push`. */
	function write(push = false) {
		clearTimeout(timer);
		const url = viewUrl();
		writes = writes.then(() => {
			if (!push && url === location.pathname + location.search) return;
			const state = { depth: (page.state.depth ?? 0) + (push ? 1 : 0) };
			return goto(url, { shallow: true, replace: !push, state, persistState: true });
		}).catch(() => { /* superseded by another navigation */ });
	}
	// Rewriting waits for a pause, because dragging the slider changes the filters faster than
	// browsers allow.
	$effect(() => {
		if (showing || closing) return;
		viewUrl();
		timer = setTimeout(() => write(), 200);
		return () => clearTimeout(timer);
	});

	/** Open a dialog, in place of any that's open, perhaps changing the metric too. */
	function open(/** @type {import('#lib/view.js').Dialog} */ d, metric = key) {
		if (d === dialog && metric === key) return;
		shown++; // Stop showing whatever the URL asked for.
		showing = false;
		if (aboutSheet(d)) pinned = true;
		write(); // Any change still to be written belongs to the entry being left.
		intro = false;
		key = metric;
		dialog = d;
		write(true);
	}
	/** Close the dialog, however many were opened to get to it. */
	function close() {
		if (!dialog) return;
		const depth = intro ? 0 : (page.state.depth ?? 0);
		dialog = null;
		intro = false;
		if (!depth) return;
		// The entry gone back to then takes on what's on show now.
		closing = true;
		clearTimeout(timer);
		history.go(-depth);
	}
	// A dialog that closes because another has replaced it mustn't close its replacement.
	const closed = (/** @type {import('#lib/view.js').Dialog} */ d) => { if (dialog === d) close(); };

	let shown = 0;
	/** Show what the URL asks for. */
	async function show(first = false) {
		const mine = ++shown;
		showing = true;
		const view = parseView(location.search);
		filters = view.filters;
		if (view.metric) key = view.metric;
		else if (first) key = PICKABLE[Math.floor(Math.random() * PICKABLE.length)];
		let found = !!view.sheet && view.sheet === sheet.id;
		if (view.sheet && !found) {
			found = await loadSheet(view.sheet);
			if (mine !== shown) return;
			if (found) source = 'linked';
		}
		if (found || !view.sheet) pinned = found;
		// Without a scoresheet (or with one that doesn't exist), a dialog about one has nothing to show.
		const d = aboutSheet(view.dialog) && !found ? null : view.dialog;
		if (first && !d) showIntro();
		else { intro = false; dialog = d; }
		showing = false;
		if (first && !found) pickRandomSheet();
	}
	/** The intro opens by itself on a first visit only. */
	function showIntro() {
		try {
			if (localStorage.getItem(INTRO_SEEN)) return;
			localStorage.setItem(INTRO_SEEN, '1');
			dialog = 'about';
			intro = true;
		} catch { /* storage blocked: skip the intro */ }
	}

	// Back and Forward. (SvelteKit's afterNavigate doesn't run for all of them.)
	function onpopstate() {
		if (location.pathname !== home) return; // to another page
		clearTimeout(timer);
		if (closing) closing = false;
		else show();
	}
	// A link to this page, such as the title's.
	afterNavigate((nav) => {
		if (nav.type === 'link' && nav.from?.route.id === nav.to?.route.id) show();
	});

	let mounted = $state(false);
	const LIMITS_ACKED = 'wcs-explore-limitations-acknowledged';
	/** Whether the reader has acknowledged the limitations, which they must do once before closing them. */
	let acked = $state(false);
	function acknowledge() {
		acked = true;
		try { localStorage.setItem(LIMITS_ACKED, '1'); } catch { /* storage blocked: asked again next visit */ }
		close();
	}
	let app = $state(false);
	onMount(() => {
		mounted = true;
		try { acked = !!localStorage.getItem(LIMITS_ACKED); } catch { /* ask */ }
		show(true);
		explorer.open = open;
		const mq = matchMedia(APP_QUERY);
		const sync = () => (app = mq.matches);
		sync();
		mq.addEventListener('change', sync);
		return () => {
			explorer.open = null;
			mq.removeEventListener('change', sync);
		};
	});

	// ← and → step through the metrics, unless a dialog is open or the reader is typing.
	const onKey = (/** @type {KeyboardEvent} */ e) => {
		if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
		if (dialog) return;
		if (/** @type {HTMLElement} */ (e.target).closest('input, select, textarea')) return;
		if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
		else if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
	};

	// The scoresheet "How is this calculated?" works through, and whose profile can be opened: one chosen at random on load
	// (the fallback until it arrives), the one picked in the "Highlighted scoresheet" box, or the
	// one whose point was clicked in the box plot, or the one the URL names.
	let sheet = $derived(/** @type {import('#lib/server/data.js').Profile} */ (data.fallback));
	let source = $state(/** @type {'random' | 'picked' | 'clicked' | 'linked'} */ ('random'));
	let loading = $state(false);
	let request = 0;
	// Whether it loaded, and no other was asked for meanwhile.
	async function loadSheet(/** @type {string} */ id) {
		const mine = ++request;
		loading = true;
		try {
			const res = await fetch(link(`/data/${id}.json`));
			const loaded = res.ok ? await res.json() : undefined;
			if (!loaded || mine !== request) return false;
			if (loaded.format !== data.format) {
				// Only a link can ask for one: take it to the page for that format, and leave this one be.
				shown++;
				goto(link(FORMATS[/** @type {'jnj'|'strictly'} */ (loaded.format)].path) + location.search, { replace: true });
				return false;
			}
			sheet = loaded;
			return true;
		} finally {
			if (mine === request) loading = false;
		}
	}
	async function pickRandomSheet() {
		// Drawn from the finals on show, if there are any.
		const ids = (filtered.length ? filtered : rows).map((/** @type {any} */ r) => r.id).filter((/** @type {string} */ id) => id !== sheet.id);
		if (ids.length && await loadSheet(ids[Math.floor(Math.random() * ids.length)])) source = 'random';
	}
	async function pickSheet(/** @type {string} */ id) {
		if (!(await loadSheet(id))) return;
		source = 'picked';
		pinned = true;
	}
	// A click on a point in the box plot shows that scoresheet's calculation.
	async function showSheet(/** @type {string} */ id) {
		if (id !== sheet.id && !(await loadSheet(id))) return;
		source = 'clicked';
		open('working');
	}
	// A click on a metric in a scoresheet's profile shows its working.
	const showMetric = (/** @type {string} */ k) => open('working', k);
	// A metric named in prose: it becomes the current metric, wherever the reader is. In the working it's
	// shown in place; from a profile, that leads to its working; elsewhere any dialog closes, to show the chart.
	setContext('showMetric', (/** @type {string} */ k) => {
		if (dialog === 'working') key = k;
		else if (dialog === 'profile') open('working', k);
		else {
			close();
			key = k;
		}
	});
	/** Why a scoresheet isn't in the charts on show, or '' if it is. */
	const uncharted = (/** @type {import('#lib/dimensions.js').Countable} */ r) =>
		r.n < (meta.minN ?? 0) ? 'has too few finalists for this metric' : matches(r, filters) ? '' : 'is outside the filters';
	const sheetCharted = $derived(!uncharted({ m: sheet.judges.length, n: sheet.competitors.length, country: sheet.country, date: sheet.date }));
</script>

<svelte:window onkeydown={onKey} {onpopstate} />

{#snippet metricOptions(full = false)}
	{#each FAMILIES as f (f.id)}
		<optgroup label={f.title}>
			{#each f.metrics as k (k)}<option value={k}>{full ? METRICS[k].label : (METRICS[k].menu ?? METRICS[k].label)}</option>{/each}
		</optgroup>
	{/each}
{/snippet}

<div class="explorer" class:app>
	<header class="topbar">
		<a class="brand" href={link('/')}>WCS judge agreement{#if DRAFT}<span class="draft-tag">DRAFT</span>{/if}</a>
		<div class="formats" role="group" aria-label="Dance format">
			{#each Object.values(FORMATS) as f (f.id)}
				<a href="{link(f.path)}?{query}" aria-current={f.id === data.format ? 'page' : undefined}
					style:--c={f.colour}>{f.label}</a>
			{/each}
		</div>
		<span class="count small muted">{anyFilters(filters) ? `${filtered.length} of ` : ''}{rows.length} finals, {date(data.info.first_event)} to {date(data.info.last_event)}</span>
		<span class="spacer"></span>
		<button type="button" class="warn" onclick={() => open('limitations')}>⚠ Exploratory: read the limitations</button>
		<button type="button" class="link-btn" onclick={() => open('about')}>About</button>
	</header>

	<div class="body">
		<nav class="rail" aria-label="Metrics">
			<label class="select">
				<span class="small muted">Metric</span>
				<select bind:value={key}>{@render metricOptions()}</select>
			</label>
			<div class="list">
				<h2 class="rail-title">Metrics</h2>
				{#each FAMILIES as f (f.id)}
					<div class="fam">
						<div class="fam-title">{f.title}</div>
						{#each f.metrics as k (k)}
							<button type="button" class:hidden-metric={METRICS[k].hidden} aria-pressed={k === key} onclick={() => (key = k)}>
								{METRICS[k].menu ?? METRICS[k].label}
							</button>
						{/each}
					</div>
				{/each}
			</div>
		</nav>

		<section class="view">
			<div class="head">
				<div class="heading">
					<div class="title">
						<h1 class="metric">{meta.label}</h1>
						<button type="button" class="btn primary" onclick={() => open('working')}>How is this calculated?</button>
					</div>
					<p class="direction small">
						<span class="dot" class:ok={meta.higher} class:bad={!meta.higher}></span>
						{meta.higher ? 'Higher' : 'Lower'} means more agreement{#if meta.minN}{' · '}finals of {meta.minN} or more competitors{/if}
					</p>
					<div class="filters"><FilterBar bind:filters /></div>
				</div>
				<SheetPicker {rows} selected={mounted ? sheet.id : undefined} {uncharted} onpick={pickSheet} ondetails={() => open('profile')} />
			</div>

			<div class="charts">
				{#key key}
					<MetricChart {rows} index={METRIC_KEYS.indexOf(key)} {meta} colour={fmt.colour} {filters} fill={app}
						highlight={mounted && sheetCharted ? sheet.id : undefined} onpoint={showSheet} />
				{/key}
			</div>

			<div class="panels">
				<div class="panel">
					<h2>What it measures</h2>
					<p><Linked text={about.what} /></p>
					<p>
						<Linked text={about.reading} />
						<button type="button" class="link-btn" onclick={() => open('working')}>Learn more</button>
					</p>
				</div>
				<div class="panel">
					<h2>Caveats for this metric</h2>
					{#if about.caveats.length}
						<ul>{#each about.caveats as c, i (i)}<li><Linked text={c} /></li>{/each}</ul>
					{/if}
					<p class="small muted">
						{about.caveats.length ? 'Also see the' : 'See the'}
						<button type="button" class="link-btn" onclick={() => open('limitations')}>limitations</button>.
					</p>
				</div>
			</div>
		</section>
	</div>
</div>

{#snippet metricHeading()}
	<select class="pick-metric" aria-label="Metric" bind:value={key}>{@render metricOptions(true)}</select>
{/snippet}

<Modal bind:open={() => dialog === 'working', () => closed('working')} kicker="How is this calculated?" title={meta.label}
	heading={metricHeading} view={key} wide>
	<p class="sheet">
		<strong>{sheet.name}</strong> ({date(sheet.date)})
	</p>
	<p class="sheet-links small">
		{{ random: 'A scoresheet chosen at random.', picked: 'The scoresheet you chose.', clicked: 'The scoresheet you clicked.', linked: '' }[source]}
		To see another, close this and choose an event or click a point in the box plot, or
		<button type="button" class="link-btn" onclick={pickRandomSheet} disabled={loading}>{loading ? 'loading…' : 'pick one at random'}</button>.
		You can also <!-- An anchor, not a button, so that this long link can wrap across lines. -->
		<a href="#profile" class="link-btn" onclick={(e) => { e.preventDefault(); open('profile'); }}>see details and other metrics for this scoresheet</a>.
	</p>
	<Standing {sheet} metric={key} />
	{#key `${sheet.id}/${key}`}<Worked {sheet} focus={key} />{/key}
</Modal>

{#snippet profileHeading()}
	<SheetPicker compact {rows} selected={mounted ? sheet.id : undefined} {uncharted} onpick={pickSheet} />
{/snippet}

<Modal bind:open={() => dialog === 'profile', () => closed('profile')} kicker="Scoresheet profile" title={sheet.name} heading={profileHeading} wide>
	<SheetMeta {sheet} />
	<RankMatrix {sheet} caption="Each judge’s ranks (1 = first), competitors in the order on the scoresheet" />
	<h3>Every metric for this scoresheet</h3>
	<p class="small">
		Choose a metric to see its working. A <span class="tick">✓</span> means that recalculating it in your browser
		gives the value used in the charts. The percentile compares this final with all {fmt.label} finals, at every
		level and whatever the filters: 100th is the most agreement, whichever way the metric runs. It isn’t adjusted for
		field or panel size, so for example a small final tends to rank high on the metrics measured in places.
	</p>
	<MetricsTable {sheet} percentiles={sheet.percentiles} current={key} onmetric={showMetric} />
</Modal>

<Modal bind:open={() => dialog === 'limitations', () => closed('limitations')} locked={!acked} kicker="Before you read anything into this" title="Reasons these comparisons might mislead">
	<Limitations info={data.info} />
	<p class="ack"><button type="button" class="btn danger" onclick={acknowledge}>I understand and promise to take care with interpreting this</button></p>
</Modal>

<Modal bind:open={() => dialog === 'about', (v) => { if (!v && dialog === 'about') open('limitations'); }} kicker="About" title="How much do WCS judges disagree?">
	<p class="byline">By Chuan-Zheng Lee<span class="credit">, with implementation by Claude</span></p>
	<p>
		In a West Coast Swing final, every judge ranks every competitor, and relative placement combines those
		rankings into the result. This looks at the rankings before they’re combined: how different are the
		judges’ rankings from each other, and does that vary by division level? It covers
		<strong>{rows.length} {fmt.label} finals</strong> from {date(data.info.first_event)} to
		{date(data.info.last_event)}.{#if other}
			{' '}<a href="{link(other.path)}?{query}">{other.label} finals</a> are a click away in the top bar.{/if}
	</p>
	<p>
		There are many ways to measure how far apart rankings are, and they don’t all answer the same question.
		This uses eleven, in four families. Pick one on the left (or step through them with ← and →); the bar
		chart shows its mean by level, and the box plot shows every final. Field and panel sizes differ between
		levels, so you can narrow the charts to finals with similar numbers of finalists or judges; the vertical
		axes stay put, so you can compare. The address in your browser always links to what you’re looking at.
	</p>
	<p>
		Every number can be checked. “How is this calculated?” recalculates the metric in your browser, step by
		step, and checks the result against the analysis. Choose a scoresheet to highlight at the top right, to ring it
		in the box plot and work through it; its “details” show the judges’ rankings, every metric and a link to
		the published scoresheet. Or click a point in the box plot for its working.
	</p>
	<p>
		The method and design decisions are mine; the code, including the data processing and this website,
		was largely written by <a href="https://claude.ai/">Claude</a>, under my direction.
	</p>
	<p>
		Data: published finals scoresheets from <a href="https://scoring.dance/">scoring.dance</a>,
		<a href="https://eepro.com/">eepro.com</a> and <a href="https://danceconvention.net/">danceconvention.net</a>,
		events {date(data.info.first_event)} to {date(data.info.last_event)}; {data.info.sheets} scoresheets,
		exported {date(data.info.exported)} from commit <code>{data.info.commit}</code>. Code:
		<a href="https://github.com/czlee/wcs">czlee/wcs</a>.
	</p>
	<p class="callout small">
		<strong>This is exploratory.</strong> Panel and field sizes differ between levels, and most of these
		metrics depend on them. <button type="button" class="link-btn" onclick={() => open('limitations')}>Read the limitations</button>
		before reading anything into a difference.
	</p>
	<p><button type="button" class="btn primary" onclick={() => open('limitations')}>Continue</button></p>
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
	.formats { display: flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
	.formats a { text-align: center; padding: 0.2em 0.8em; font-size: 0.86rem; text-decoration: none; color: var(--text-2); }
	.formats a + a { border-left: 1px solid var(--border); }
	.formats a[aria-current='page'] { background: var(--c); color: #fff; font-weight: 600; }
	.warn {
		font: inherit; font-size: 0.82rem; cursor: pointer; padding: 0.2em 0.7em; border-radius: 4px;
		border: 1px solid var(--warn-border); background: var(--warn-bg); color: var(--warn-text);
	}
	.ack { margin: 1.2em 0 0; text-align: center; }
	.btn.danger {
		font: inherit; font-weight: 600; cursor: pointer; padding: 0.55em 1.1em; border-radius: 6px;
		border: 1px solid #8f1d12; background: #c0392b; color: #fff;
	}
	.btn.danger:hover { background: #a93226; }
	.link-btn { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
	.topbar .link-btn { font-size: 0.85rem; color: var(--text-2); }

	.body { display: grid; grid-template-columns: 12em minmax(0, 1fr); gap: 1.4em; margin-top: 1em; }
	.select { display: none; }
	.select select { font: inherit; width: 100%; padding: 0.3em; margin-top: 0.2em; }
	.list { display: flex; flex-direction: column; gap: 0.7em; }
	.rail-title { font-size: 1rem; margin: 0 0 -0.3em; }
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
	.head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: start; gap: 0.6em 1.5em; margin-bottom: 0.6em; padding-bottom: 0.6em; border-bottom: 1px solid var(--border); }
	h1.metric { margin: 0 0 0.1em; font-size: 1.5rem; }
	.direction { margin: 0; color: var(--text-2); }
	.dot { display: inline-block; width: 0.6em; height: 0.6em; border-radius: 50%; margin-right: 0.2em; }
	.dot.ok { background: var(--ok); }
	.dot.bad { background: var(--bad); }
	/* The title wraps before the scoresheet box is pushed under it. */
	.heading { flex: 1 1 18em; }
	.title { display: flex; flex-wrap: wrap; align-items: center; gap: 0.2em 0.9em; }
	.title .btn { font-size: 0.75rem; padding: 0.175em 0.75em; }
	.filters { margin-top: 0.5em; }
	.btn.primary { font-weight: 600; border-color: var(--accent); color: var(--accent); }

	.panels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8em; margin-top: 0.8em; }
	.panel { border: 1px solid var(--border); border-radius: 6px; padding: 0.35em 0.8em 0.4em; font-size: 0.82rem; line-height: 1.45; }
	.panel h2 { margin: 0.15em 0 0.25em; font-size: 0.85rem; }
	.panel p, .panel li { margin: 0.3em 0; max-width: none; }
	.panel .small { font-size: 0.78rem; }
	.panel ul { margin: 0.25em 0; padding-left: 1.2em; }
	.panel li + li { margin-top: 0.2em; }

	/* The metric's name in the dialog's title, as a dropdown (as wide as its longest option). */
	.pick-metric {
		font: inherit; max-width: 100%; margin: 0 0 0 -0.3em; padding: 0.05em 0.5em 0.05em 0.2em; text-overflow: ellipsis;
		color: inherit; background: var(--surface); border: 1px solid var(--border); border-radius: 5px; cursor: pointer;
	}
	.pick-metric:hover { border-color: var(--text-3); }
	.sheet { margin-bottom: 0.1em; }
	.tick { color: var(--ok); }
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
