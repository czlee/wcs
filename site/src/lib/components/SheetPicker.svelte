<script>
	// A box that chooses a scoresheet: type to search by event, division, date or place
	// (see lib/fuzzy.js), and pick from the list. It takes effect at once, through `onpick`.
	import { tick } from 'svelte';
	import { haystack, match, queryWords, runs } from '#lib/fuzzy.js';
	import { LEVELS, LEVEL_LABEL } from '#lib/levels.js';
	import { place } from '#lib/places.js';
	import { date } from '#lib/format.js';
	import Term from './Term.svelte';

	/**
	 * @typedef {{id: string, level: string, event: string, date: string, name: string, m: number, n: number,
	 *   country: string | null, state: string | null}} Row
	 * @typedef {{row: Row, title: string, division: string, details: string, hay: ReturnType<typeof haystack>}} Item
	 * @typedef {{item: Item, hits: Set<number>[]}} Result
	 */
	/**
	 * `uncharted` says why a scoresheet isn't in the charts on show (a phrase that follows
	 * "this scoresheet"), or '' if it is.
	 * @type {{rows: Row[], selected?: string, uncharted: (r: Row) => string, onpick: (id: string) => void, ondetails: () => void}}
	 */
	let { rows, selected, uncharted, onpick, ondetails } = $props();
	const MAX_SHOWN = 50;
	const id = $props.id();

	const tidy = (/** @type {string} */ s) => s.normalize('NFC').replaceAll('’', "'").replace(/\s+/g, ' ').trim();

	/** The event's name with its year, which some names have already (as 2025 or '25). */
	const titleOf = (/** @type {Row} */ r) => {
		const event = tidy(r.event), year = r.date.slice(0, 4);
		return /\b20\d\d\b|'\d\d\b/.test(event) ? event : `${event} ${year}`;
	};
	/** The competition's name without the event's, the year or "final", which the title covers. */
	const divisionOf = (/** @type {Row} */ r) => {
		const name = tidy(r.name), event = tidy(r.event);
		const i = name.toLowerCase().indexOf(event.toLowerCase());
		const rest = i < 0 ? name : name.slice(0, i) + name.slice(i + event.length);
		const parts = rest.split(/(?:^|\s+)-(?:\s+|$)/).map((p) => p.trim()).filter((p) => p && !/^(20\d\d|finals?)$/i.test(p));
		return parts.join(', ').replace(/\s+finals?$/i, '') || LEVEL_LABEL[r.level];
	};

	// Newest first; within an event, highest level first.
	const levelOrder = Object.fromEntries(LEVELS.map((l, i) => [l.id, i]));
	/** @type {Item[]} */
	const items = $derived(rows.map((row) => {
		const title = titleOf(row), division = divisionOf(row);
		const details = [date(row.date), place(row.country, row.state)].filter(Boolean).join(' · ');
		const hay = haystack([{ text: title }, { text: LEVEL_LABEL[row.level] }, { text: division, weight: 0.95 }, { text: details, weight: 0.85 }]);
		return { row, title, division, details, hay };
	}).sort((a, b) => (a.row.date < b.row.date ? 1 : a.row.date > b.row.date ? -1 :
		a.title.localeCompare(b.title) || levelOrder[b.row.level] - levelOrder[a.row.level])));
	const size = (/** @type {Row} */ r) => `${r.m} judges, ${r.n} finalists`;

	const current = $derived(items.find((it) => it.row.id === selected));
	const label = $derived(current ? `${current.title}, ${LEVEL_LABEL[current.row.level]}` : '');

	let open = $state(false);
	/** What's been typed, or null if nothing has been since the box was opened. */
	let query = $state(/** @type {string | null} */ (null));
	let active = $state(0);
	/** @type {HTMLInputElement | undefined} */
	let input = $state();
	/** @type {HTMLElement | undefined} */
	let list = $state();

	/** Nothing is listed until this many characters have been typed. */
	const MIN_QUERY = 3;
	const searching = (/** @type {string[][]} */ words) => words.reduce((n, w) => n + w.length, 0) >= MIN_QUERY;

	/** @type {Result[]} */
	const results = $derived.by(() => {
		if (!open) return [];
		const words = queryWords(query ?? '');
		if (!searching(words)) return [];
		return items
			.flatMap((item) => {
				const m = match(words, item.hay);
				return m ? [{ item, hits: m.hits, score: m.score }] : [];
			})
			// The sort is stable, so ties stay newest first. Rounding ties near-equal scores.
			.sort((a, b) => Math.round(10 * b.score) - Math.round(10 * a.score));
	});
	const shown = $derived(results.slice(0, MAX_SHOWN));

	function show() {
		if (open) return;
		open = true;
		query = null;
		active = -1;
	}
	function close() {
		open = false;
		query = null;
	}
	// While nothing's been typed, the name stays selected, so that typing replaces it (also
	// after a choice or Esc, when the name changes or comes back).
	$effect(() => {
		if (label && query === null && input && document.activeElement === input) input.select();
	});
	function pick(/** @type {Result | undefined} */ r) {
		if (!r) return;
		close();
		if (r.item.row.id !== selected) onpick(r.item.row.id);
	}
	async function move(/** @type {number} */ to) {
		active = Math.max(0, Math.min(to, shown.length - 1));
		await tick();
		list?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' });
	}
	function onkeydown(/** @type {KeyboardEvent} */ e) {
		if (e.isComposing) return;
		if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
			e.preventDefault();
			if (!open) show();
			else move(active + (e.key === 'ArrowDown' ? 1 : -1));
		} else if (e.key === 'Enter' && open) {
			e.preventDefault();
			pick(shown[active]);
		} else if (e.key === 'Escape' && open) {
			e.preventDefault();
			close();
		}
	}
	function oninput(/** @type {Event & {currentTarget: HTMLInputElement}} */ e) {
		open = true;
		query = e.currentTarget.value;
		active = 0;
		list?.scrollTo(0, 0);
	}
</script>

{#snippet marked(/** @type {string} */ text, /** @type {Set<number> | undefined} */ hits)}{#each runs(text, hits) as r, i (i)}{#if r.hit}<mark>{r.text}</mark>{:else}{r.text}{/if}{/each}{/snippet}

<div class="picker">
	<label for="{id}-input">
		<svg width="13" height="13" viewBox="0 0 13 13" aria-hidden="true"><circle cx="6.5" cy="6.5" r="5.2" /></svg>
		Highlighted scoresheet
	</label>
	<div class="box">
		<input bind:this={input} id="{id}-input" type="text" role="combobox" autocomplete="off" spellcheck="false"
			placeholder="Choose an event…" aria-autocomplete="list" aria-expanded={open} aria-controls="{id}-list"
			aria-activedescendant={open && shown[active] ? `${id}-${active}` : undefined} aria-describedby="{id}-details"
			value={query ?? label} {oninput} {onkeydown} onblur={close}
			onfocus={(e) => { show(); e.currentTarget.select(); }}
			onclick={(e) => { show(); if (query === null) e.currentTarget.select(); }} />
		{#if open}
			<!-- Pressing the mouse here mustn't take the focus, which would close the list. -->
			<div class="drop" role="presentation" onmousedown={(e) => e.preventDefault()}>
				{#if shown.length}
				<ul id="{id}-list" role="listbox" aria-label="Scoresheets" bind:this={list}>
					{#each shown as r, i (r.item.row.id)}
						{@const why = uncharted(r.item.row)}
						<!-- The keyboard is handled by the input, which keeps the focus. -->
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<li id="{id}-{i}" role="option" aria-selected={i === active} class:current={r.item.row.id === selected} class:dim={why}
							onclick={() => { pick(r); input?.blur(); }}>
							<span class="title">{@render marked(r.item.title, r.hits[0])}</span>
							<span class="level">{@render marked(LEVEL_LABEL[r.item.row.level], r.hits[1])}</span>
							<span class="sub">
								{#if why}<em>Not in the current view ({why})</em>{' · '}{/if}{@render marked(r.item.division, r.hits[2])} · {@render marked(r.item.details, r.hits[3])} · {size(r.item.row)}
							</span>
						</li>
					{/each}
				</ul>
				{/if}
				<p class="foot" role="status">
					{#if !searching(queryWords(query ?? ''))}Type at least {MIN_QUERY} characters to find a scoresheet
					{:else if !results.length}No matching scoresheets
					{:else if results.length > MAX_SHOWN}{MAX_SHOWN} of {results.length} scoresheets: type to narrow the list
					{:else}{results.length} scoresheet{results.length === 1 ? '' : 's'}{/if}
				</p>
			</div>
		{/if}
	</div>
	<p class="details" id="{id}-details">
		{#if current}
			{@const why = uncharted(current.row)}
			{#if why}<span class="why"><Term tip="No point in the box plot is ringed, because this scoresheet {why}.">Not in the current view</Term></span>{' · '}{/if}{current.details} · {size(current.row)}
		{:else}&nbsp;{/if}
	</p>
	<p class="more"><button type="button" class="open" disabled={!current} onclick={ondetails}>details and all metrics for this scoresheet</button></p>
</div>

<style>
	.picker { width: 25em; max-width: 100%; font-size: 0.82rem; }
	.box { position: relative; margin: 0.2em 0; }
	.open { font: inherit; padding: 0; border: 0; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; }
	label { display: flex; align-items: baseline; gap: 0.4em; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-3); }
	label svg { align-self: center; fill: none; stroke: var(--text); stroke-width: 1.8; }
	input {
		box-sizing: border-box; width: 100%; margin: 0; padding: 0.3em 0.55em; font: inherit; font-size: 0.9rem;
		text-overflow: ellipsis; color: var(--text); background: var(--surface-2); border: 1px solid var(--border); border-radius: 5px;
	}
	.details { margin: 0; max-width: none; color: var(--text-2); font-size: 0.78rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.more { margin: 0.1em 0 0; }
	.why { color: var(--warn-text); }
	.drop {
		position: absolute; z-index: 30; right: 0; top: calc(100% + 3px); width: 36em; max-width: calc(100vw - 32px);
		border: 1px solid var(--border); border-radius: 6px; background: var(--surface); box-shadow: 0 6px 20px rgb(0 0 0 / 0.25);
	}
	ul + .foot { border-top: 1px solid var(--border); }
	ul { list-style: none; margin: 0; padding: 0.25em; max-height: min(26em, 55vh); overflow-y: auto; }
	li { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0 1em; padding: 0.3em 0.55em; border-radius: 4px; cursor: pointer; line-height: 1.35; }
	li + li { margin-top: 1px; }
	li:hover { background: var(--surface-2); }
	li[aria-selected='true'] { background: var(--surface-2); box-shadow: inset 3px 0 0 var(--accent); }
	.title { font-weight: 600; color: var(--text); }
	.level { color: var(--text-2); }
	.sub { grid-column: 1 / -1; font-size: 0.76rem; color: var(--text-3); }
	.current .title::after { content: ' ✓'; color: var(--accent); }
	.dim .title, .dim .level { color: var(--text-3); }
	mark { color: inherit; background: var(--highlight-bg); border-radius: 2px; }
	.foot { margin: 0; max-width: none; padding: 0.3em 0.8em; color: var(--text-3); font-size: 0.76rem; }
	@media (max-width: 860px) {
		.picker { width: 100%; }
		.drop { left: 0; right: 0; width: auto; }
	}
</style>
