<script>
	// Every scoresheet on the site, filterable by format, level and text. Filters
	// come from the URL (?format=jnj&level=adv) so the charts can link here.
	import { onMount } from 'svelte';
	import { FORMATS, LEVELS, LEVEL_LABEL } from '#lib/levels.js';
	import { link, date } from '#lib/format.js';

	let { data } = $props();
	let format = $state('');
	let level = $state('');
	let q = $state('');
	onMount(() => {
		const p = new URLSearchParams(location.search);
		format = p.get('format') ?? '';
		level = p.get('level') ?? '';
		q = p.get('q') ?? '';
	});
	// Keep the URL in step, so a filtered list can be shared.
	$effect(() => {
		const p = new URLSearchParams();
		if (format) p.set('format', format);
		if (level) p.set('level', level);
		if (q) p.set('q', q);
		const s = p.toString();
		history.replaceState(history.state, '', s ? `?${s}` : location.pathname);
	});
	const shown = $derived.by(() => {
		const words = q.toLowerCase().split(/\s+/).filter(Boolean);
		return data.list.filter((/** @type {any} */ s) =>
			(!format || s.format === format) && (!level || s.level === level) &&
			words.every((w) => (s.event + ' ' + s.name).toLowerCase().includes(w)));
	});
</script>

<svelte:head>
	<title>All scoresheets · WCS judge divergence</title>
	<meta name="description" content="Every finals scoresheet in the WCS judge divergence analysis, each with its full working." />
</svelte:head>

<h1>All scoresheets</h1>
<p>Every scoresheet in the analysis. Each one opens with its source and every metric worked through.</p>

<div class="filters">
	<label>Format
		<select bind:value={format}>
			<option value="">Both</option>
			{#each Object.values(FORMATS) as f (f.id)}<option value={f.id}>{f.label}</option>{/each}
		</select>
	</label>
	<label>Level
		<select bind:value={level}>
			<option value="">All</option>
			{#each LEVELS as l (l.id)}<option value={l.id}>{l.label}</option>{/each}
		</select>
	</label>
	<label class="search">Search
		<input type="search" bind:value={q} placeholder="Event or division name" />
	</label>
</div>
<p class="small muted">{shown.length} of {data.list.length} scoresheets</p>

<div class="table-wrap">
	<table>
		<thead><tr><th>Date</th><th>Event</th><th>Division</th><th>Counted as</th><th class="num">Judges</th><th class="num">Comp.</th></tr></thead>
		<tbody>
			{#each shown as s (s.id)}
				<tr>
					<td class="nowrap">{date(s.date)}</td>
					<td>{s.event}</td>
					<td><a href={link(`/sheet/${s.id}/`)}>{s.name}</a></td>
					<td class="nowrap">{FORMATS[/** @type {'jnj'|'strictly'} */ (s.format)].label}, {LEVEL_LABEL[s.level]}</td>
					<td class="num">{s.m}</td>
					<td class="num">{s.n}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.filters { display: flex; flex-wrap: wrap; gap: 0.6em 1.2em; align-items: end; margin: 1em 0 0.4em; }
	label { display: flex; flex-direction: column; font-size: 0.8rem; color: var(--text-3); gap: 0.15em; }
	select, input { font: inherit; font-size: 0.9rem; padding: 0.25em 0.4em; border: 1px solid var(--border); border-radius: 5px; background: var(--surface-2); color: var(--text); }
	.search { flex: 1 1 14em; }
	.nowrap { white-space: nowrap; }
</style>
