<script>
	// One metric, by division level: mean ± interval bars (left) and box plot with
	// every scoresheet as a point (right). Points open that scoresheet's working.
	import { scaleBand, scaleLinear } from 'd3-scale';
	import { onMount } from 'svelte';
	import { LEVELS } from '#lib/levels.js';
	import { meanCI, boxStats, CI_LABEL, MIN_CELL } from '#lib/stats.js';
	import { matches, noFilters } from '#lib/dimensions.js';
	import { fx, minus, date } from '#lib/format.js';
	import Term from './Term.svelte';

	/** @typedef {{id: string, level: string, event: string, date: string, name: string, m: number, n: number, country: string | null, v: (number | null)[]}} Row */
	/**
	 * @type {{rows: Row[], index: number, meta: {label: string, higher: boolean, chance?: boolean}, colour: string,
	 *   filters?: import('#lib/dimensions.js').Filters, highlight?: string, fill?: boolean, onpoint: (id: string) => void}}
	 */
	// `filters` picks which scoresheets are drawn. The axes come from all of `rows`, so
	// views with different filters can be compared by eye.
	// `onpoint` is called with a point's scoresheet id when it's clicked.
	// `highlight`, a scoresheet id, rings that scoresheet's point (the explorer's highlighted scoresheet).
	// With `fill`, the charts take the size of their container (which must have a height) and
	// draw at true pixel size; otherwise they keep a fixed shape and scale with the width.
	let { rows: allRows, index, meta, colour, filters = noFilters(), highlight, fill = false, onpoint } = $props();
	// Scoresheets with no value for this metric (a field below its minN) are left out.
	const unfiltered = $derived(allRows.filter((r) => r.v[index] != null));
	const rows = $derived(unfiltered.filter((r) => matches(r, filters)));
	const val = (/** @type {Row} */ r) => /** @type {number} */ (r.v[index]);

	let mw = $state(0), mh = $state(0);
	const W = $derived(fill && mw > 200 ? mw : 460);
	const H = $derived(fill && mh > 120 ? mh : 240);
	const R = $derived(fill ? 3 : 2.4);
	// The right margin holds the agreement strip: a green-to-red bar showing which
	// way along the y-axis the judges agree more, labelled at both ends.
	const M = { t: 12, r: 30, b: 40, l: 46 };
	const STRIP = $derived({ x: W - 24, w: 6 });
	const gid = $props.id();
	const x = $derived(scaleBand().domain(LEVELS.map((l) => l.id)).range([M.l, W - M.r]).padding(0.28));

	const cells = (/** @type {Row[]} */ from) => LEVELS.map((l) => {
		const pts = from.filter((r) => r.level === l.id);
		const vals = pts.map(val);
		const small = pts.length < MIN_CELL;
		const ci = meanCI(vals);
		// Too few scoresheets for an interval or a box to mean much: show the mean and the points alone.
		if (small) ci.lo = ci.hi = NaN;
		return { level: l, pts, ci, small, box: boxStats(vals), colour: small ? 'var(--text-3)' : colour };
	});
	const byLevel = $derived(cells(rows));
	const byLevelAll = $derived(cells(unfiltered));
	const smallNote = `Fewer than ${MIN_CELL} scoresheets`;

	const barY = $derived.by(() => {
		// Fixed by the unfiltered bars, unless a filtered bar or interval needs more room. Grey
		// bars don't count (they're clipped), so a handful of finals can't stretch the axis.
		const all = [...byLevelAll, ...byLevel];
		const big = all.filter((d) => !d.small);
		const ends = (big.length ? big : all).flatMap((d) => [d.ci.mean, d.ci.lo, d.ci.hi]).filter(Number.isFinite);
		const lo = Math.min(0, ...ends);
		const hi = Math.max(0, ...ends);
		return scaleLinear().domain([lo, hi]).nice(5).range([H - M.b, M.t]);
	});
	const boxY = $derived.by(() => {
		const vals = unfiltered.map(val);
		return scaleLinear().domain([Math.min(...vals), Math.max(...vals)]).nice(5).range([H - M.b, M.t]);
	});

	/** A deterministic jitter in [−0.5, 0.5) from the scoresheet id, so points don't move between renders. */
	const jitter = (/** @type {string} */ id) => {
		let h = 2166136261;
		for (let i = 0; i < id.length; i++) h = Math.imul(h ^ id.charCodeAt(i), 16777619);
		return ((h >>> 0) % 1000) / 1000 - 0.5;
	};

	/** Bar outline with rounded corners at the data end only (not at the baseline). */
	const bar = (/** @type {number} */ x0, /** @type {number} */ w, /** @type {number} */ y0, /** @type {number} */ y1) => {
		const r = Math.min(4, w / 2, Math.abs(y1 - y0));
		if (y1 <= y0) return `M${x0},${y0}V${y1 + r}Q${x0},${y1} ${x0 + r},${y1}H${x0 + w - r}Q${x0 + w},${y1} ${x0 + w},${y1 + r}V${y0}Z`;
		return `M${x0},${y0}V${y1 - r}Q${x0},${y1} ${x0 + r},${y1}H${x0 + w - r}Q${x0 + w},${y1} ${x0 + w},${y1 - r}V${y0}Z`;
	};

	let mounted = $state(false);
	onMount(() => (mounted = true));

	/** @type {{x: number, y: number, lines: string[]} | null} */
	let tip = $state(null);
	/** @type {HTMLDivElement | undefined} */
	let wrap = $state();
	const show = (/** @type {MouseEvent | FocusEvent} */ ev, /** @type {string[]} */ lines) => {
		if (!wrap) return;
		const box = wrap.getBoundingClientRect();
		const t = /** @type {Element} */ (ev.currentTarget ?? ev.target).getBoundingClientRect();
		tip = { x: t.left + t.width / 2 - box.left, y: t.top - box.top, lines };
	};
	const hide = () => (tip = null);
	const pointLines = (/** @type {Row} */ r) => [
		`${r.event}`, `${r.name}`, `${date(r.date)} · ${r.m} judges, ${r.n} competitors`,
		`${meta.label}: ${minus(fx(val(r)))}`, 'Click to see the working'
	];
	const ticks = (/** @type {any} */ y) => y.ticks(5);
	const tickFmt = (/** @type {number} */ v) => minus(String(+v.toFixed(3)));
</script>

{#snippet agreeStrip(/** @type {string} */ panel)}
	{@const top = meta.higher ? 'ok' : 'bad'}
	{@const bottom = meta.higher ? 'bad' : 'ok'}
	<g class="strip" aria-hidden="true">
		<defs>
			<linearGradient id="{gid}-{panel}-strip" x1="0" x2="0" y1="0" y2="1">
				<stop offset="0" style:stop-color="var(--{top})" />
				<stop offset="0.5" style:stop-color="var(--grid)" />
				<stop offset="1" style:stop-color="var(--{bottom})" />
			</linearGradient>
		</defs>
		<rect x={STRIP.x} y={M.t} width={STRIP.w} height={H - M.b - M.t} rx="3" fill="url(#{gid}-{panel}-strip)" />
		<text class="strip-label {top}" transform="translate({W - 14},{M.t}) rotate(90)" text-anchor="start">{meta.higher ? 'more agreement' : 'less agreement'}</text>
		<text class="strip-label {bottom}" transform="translate({W - 14},{H - M.b}) rotate(90)" text-anchor="end">{meta.higher ? 'less agreement' : 'more agreement'}</text>
	</g>
{/snippet}

{#snippet empty()}
	{#if !rows.length}
		<text class="empty" x={(M.l + W - M.r) / 2} y={(M.t + H - M.b) / 2} text-anchor="middle">No finals match these filters</text>
	{/if}
{/snippet}

<div class="chart" class:fill bind:this={wrap}>
	<div class="panels">
		<figure>
			<figcaption>{CI_LABEL} (<Term tip="Scoresheets aren’t independent: the same judges sit on many panels. The error bars are the 95% confidence interval assuming independence, so they’re probably too narrow.">provisional</Term>), by level</figcaption>
			<div class="plot" bind:clientWidth={mw} bind:clientHeight={mh}>
			<svg viewBox="0 0 {W} {H}" role="img" aria-label="{meta.label} ({meta.higher ? 'higher' : 'lower'} means more agreement): mean by level">
				<defs><clipPath id="{gid}-bars"><rect x={M.l} y={M.t} width={W - M.l - M.r} height={H - M.b - M.t} /></clipPath></defs>
				{#each ticks(barY) as t (t)}
					<line class="grid" x1={M.l} x2={W - M.r} y1={barY(t)} y2={barY(t)} />
					<text class="tick" x={M.l - 6} y={barY(t)} dy="0.32em" text-anchor="end">{tickFmt(t)}</text>
				{/each}
				{#each byLevel as d (d.level.id)}
					{@const bx = /** @type {number} */ (x(d.level.id))}
					{#if d.ci.n}
						{@const label = `${d.level.label}: mean ${minus(fx(d.ci.mean))}`}
						{@const lines = [label, d.small ? smallNote : `interval ${minus(fx(d.ci.lo))} to ${minus(fx(d.ci.hi))}`, `${d.ci.n} scoresheets`]}
						<g class="bar" role="presentation" onmouseenter={(e) => show(e, lines)} onmouseleave={hide}>
							<rect class="hit" x={bx - 4} y={M.t} width={x.bandwidth() + 8} height={H - M.b - M.t} />
							<path d={bar(bx, x.bandwidth(), barY(0), barY(d.ci.mean))} fill={d.colour} clip-path="url(#{gid}-bars)" />
							{#if Number.isFinite(d.ci.lo)}
								<line class="err" x1={bx + x.bandwidth() / 2} x2={bx + x.bandwidth() / 2} y1={barY(d.ci.lo)} y2={barY(d.ci.hi)} />
								<line class="err" x1={bx + x.bandwidth() * 0.3} x2={bx + x.bandwidth() * 0.7} y1={barY(d.ci.lo)} y2={barY(d.ci.lo)} />
								<line class="err" x1={bx + x.bandwidth() * 0.3} x2={bx + x.bandwidth() * 0.7} y1={barY(d.ci.hi)} y2={barY(d.ci.hi)} />
							{/if}
						</g>
					{/if}
					<text class="lvl" x={bx + x.bandwidth() / 2} y={H - M.b + 15} text-anchor="middle">{d.level.short}</text>
					<text class="n" x={bx + x.bandwidth() / 2} y={H - M.b + 29} text-anchor="middle">n={d.ci.n}</text>
				{/each}
				<line class="axis" x1={M.l} x2={W - M.r} y1={barY(0)} y2={barY(0)} />
				{#if meta.chance}<text class="chance" x={W - M.r - 2} y={barY(0) - 3} text-anchor="end">chance</text>{/if}
				{@render agreeStrip('bar')}
				{@render empty()}
			</svg>
			</div>
		</figure>
		<figure>
			<figcaption>Every scoresheet, with quartiles</figcaption>
			<div class="plot">
			<svg viewBox="0 0 {W} {H}" role="img" aria-label="{meta.label} ({meta.higher ? 'higher' : 'lower'} means more agreement): distribution by level">
				{#each ticks(boxY) as t (t)}
					<line class="grid" x1={M.l} x2={W - M.r} y1={boxY(t)} y2={boxY(t)} />
					<text class="tick" x={M.l - 6} y={boxY(t)} dy="0.32em" text-anchor="end">{tickFmt(t)}</text>
				{/each}
				{#each byLevel as d (d.level.id)}
					{@const bx = /** @type {number} */ (x(d.level.id))}
					{@const bw = x.bandwidth()}
					{#if d.box.n && !d.small}
						<g class="box" role="presentation"
							onmouseenter={(e) => show(e, [`${d.level.label}, ${d.box.n} scoresheets`, `median ${minus(fx(d.box.median))}`, `quartiles ${minus(fx(d.box.q1))} to ${minus(fx(d.box.q3))}`, `whiskers ${minus(fx(d.box.lowWhisker))} to ${minus(fx(d.box.highWhisker))}`])}
							onmouseleave={hide}>
							<line class="whisker" x1={bx + bw / 2} x2={bx + bw / 2} y1={boxY(d.box.lowWhisker)} y2={boxY(d.box.q1)} />
							<line class="whisker" x1={bx + bw / 2} x2={bx + bw / 2} y1={boxY(d.box.q3)} y2={boxY(d.box.highWhisker)} />
							<line class="whisker" x1={bx + bw * 0.3} x2={bx + bw * 0.7} y1={boxY(d.box.lowWhisker)} y2={boxY(d.box.lowWhisker)} />
							<line class="whisker" x1={bx + bw * 0.3} x2={bx + bw * 0.7} y1={boxY(d.box.highWhisker)} y2={boxY(d.box.highWhisker)} />
							<rect x={bx} y={boxY(d.box.q3)} width={bw} height={Math.max(1, boxY(d.box.q1) - boxY(d.box.q3))} fill={d.colour} fill-opacity="0.16" stroke={d.colour} stroke-width="1.5" rx="2" />
							<line class="median" x1={bx} x2={bx + bw} y1={boxY(d.box.median)} y2={boxY(d.box.median)} stroke={d.colour} />
						</g>
					{/if}
					{#if mounted}
						{#each d.pts as r (r.id)}
							<circle class="pt" cx={bx + bw / 2 + jitter(r.id) * bw * 0.9} cy={boxY(val(r))} r={R} fill={d.colour}
								role="button" tabindex="-1" aria-label={r.name}
								onmouseenter={(e) => show(e, pointLines(r))} onmouseleave={hide}
								onclick={() => onpoint(r.id)} onkeydown={() => {}} />
						{/each}
						{@const hr = highlight ? d.pts.find((r) => r.id === highlight) : undefined}
						{#if hr}
							<circle class="ring" cx={bx + bw / 2 + jitter(hr.id) * bw * 0.9} cy={boxY(val(hr))} r={R + 3.6} />
						{/if}
					{/if}
					<text class="lvl" x={bx + bw / 2} y={H - M.b + 15} text-anchor="middle">{d.level.short}</text>
					<text class="n" x={bx + bw / 2} y={H - M.b + 29} text-anchor="middle">n={d.box.n}</text>
				{/each}
				{#if meta.chance && boxY.domain()[0] < 0 && boxY.domain()[1] > 0}
					<line class="chance-line" x1={M.l} x2={W - M.r} y1={boxY(0)} y2={boxY(0)} />
					<text class="chance" x={W - M.r - 2} y={boxY(0) - 3} text-anchor="end">chance</text>
				{/if}
				{@render agreeStrip('box')}
				{@render empty()}
			</svg>
			</div>
		</figure>
	</div>
	{#if tip}
		<div class="tip" style:left="{tip.x}px" style:top="{tip.y}px" role="tooltip">
			{#each tip.lines as l, i (i)}<div class:first={i === 0}>{l}</div>{/each}
		</div>
	{/if}
</div>

<style>
	.chart { position: relative; }
	.panels { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.4em 1.4em; }
	@media (max-width: 760px) { .panels { grid-template-columns: minmax(0, 1fr); } }
	figure { margin: 0; min-width: 0; }
	figcaption { font-size: 0.8rem; color: var(--text-3); }
	svg { width: 100%; height: auto; display: block; overflow: visible; }
	.fill, .fill .panels { height: 100%; }
	.fill .panels { grid-template-rows: minmax(0, 1fr); }
	.fill figure { display: flex; flex-direction: column; min-height: 0; }
	.fill .plot { position: relative; flex: 1; min-height: 0; }
	.fill svg { position: absolute; inset: 0; height: 100%; }
	.fill figcaption { font-size: 0.85rem; margin-bottom: 0.2em; }
	.fill .tick, .fill .n, .fill .chance, .fill .strip-label { font-size: 11px; }
	.fill .lvl { font-size: 12.5px; }
	.grid { stroke: var(--grid); }
	.axis { stroke: var(--text-3); }
	.chance-line { stroke: var(--text-3); stroke-dasharray: 3 3; }
	.chance { font-size: 10px; fill: var(--text-3); }
	.tick, .n { font-size: 10px; fill: var(--text-3); }
	.strip-label { font-size: 10px; font-weight: 600; }
	.strip-label.ok { fill: var(--ok); }
	.strip-label.bad { fill: var(--bad); }
	.empty { font-size: 14px; fill: var(--text-2); }
	.lvl { font-size: 11.5px; fill: var(--text-2); }
	.err { stroke: var(--text); stroke-width: 1.3; }
	.hit { fill: transparent; }
	.bar:hover path { opacity: 0.85; }
	.whisker { stroke: var(--text-3); stroke-width: 1; }
	.median { stroke-width: 2.5; }
	.pt { fill-opacity: 0.38; cursor: pointer; }
	.ring { fill: none; stroke: var(--text); stroke-width: 1.8; pointer-events: none; }
	.pt:hover { fill-opacity: 1; stroke: var(--text); stroke-width: 1; }
	.tip {
		position: absolute; transform: translate(-50%, calc(-100% - 8px)); pointer-events: none; z-index: 20;
		width: max-content; max-width: min(22em, calc(100vw - 32px)); padding: 0.4em 0.6em;
		border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text-2);
		font-size: 0.8rem; line-height: 1.35; box-shadow: 0 2px 8px rgb(0 0 0 / 0.15);
	}
	.tip .first { color: var(--text); font-weight: 600; }
</style>
