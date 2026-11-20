<script>
	// The limitations box near the top of every results page. The footer links to
	// #limitations; arriving that way opens it.
	import { date } from '#lib/format.js';
	/** @type {{info: {first_event: string, last_event: string, counts: Record<string, Record<string, number>>}}} */
	let { info } = $props();
	let open = $state(false);
	$effect(() => {
		const check = () => { if (location.hash === '#limitations') open = true; };
		check();
		addEventListener('hashchange', check);
		return () => removeEventListener('hashchange', check);
	});
	const smallest = $derived(
		Object.entries(info.counts)
			.flatMap(([f, ls]) => Object.entries(ls).map(([l, n]) => ({ f, l, n })))
			.toSorted((a, b) => a.n - b.n)[0]
	);
</script>

<details class="limits" id="limitations" bind:open>
	<summary><strong>Before you read anything into this:</strong> Reasons these comparisons might mislead (a.k.a. limitations)</summary>
	<ul>
		<li>
			<strong>This is exploratory.</strong> It describes how much judges’ rankings differ, by level. It
			doesn’t explain why. Apart from a first-pass chance correction of the top-3 metrics (below), nothing
			on this site has been adjusted for the other differences between levels.
		</li>
		<li>
			<strong>Levels differ in panel size and field size, and most of these metrics depend on both.</strong>
			Kendall’s W falls with more judges even if they’re just as consistent; the rank-spread metrics grow
			with the field; and two judges’ top 3s overlap more by chance in a smaller final. The top-3 charts
			subtract that chance level, a naive first-pass correction that doesn’t remove every effect of field
			size, and leave out finals of 5, where any two top 3s must share someone. For example, Jack &amp; Jill
			Novice finals here average about 13 competitors, All-Star finals about 8. Some or all of a difference
			between levels could come from this.
		</li>
		<li>
			<strong>Scoresheets aren’t independent.</strong> The same judges sit on many panels, and several
			divisions come from the same event. The error bars assume independence, so they’re probably too
			narrow. The interval method itself (mean ± 1.96 standard errors) is provisional.
		</li>
		<li>
			<strong>Levels are read from division names</strong> by keyword. Combined divisions (e.g. “All-Star/Champions”)
			count as the higher level, and invitational or differently-named divisions may be misfiled.
		</li>
		<li>
			<strong>Not every event.</strong> Only finals published on scoring.dance, eepro.com or
			danceconvention.net, with events from {date(info.first_event)} to {date(info.last_event)}. Finals
			with tied or incomplete rankings, fewer than 3 judges or fewer than 5 competitors are left out.
			Non-WCS divisions are filtered out by keyword, so a few might remain.
		</li>
		<li>
			<strong>Finals, and rankings only.</strong> This uses each judge’s ranking of the finalists, not raw
			scores (where a scoresheet has them) or the final relative-placement result.
		</li>
		<li>
			<strong>Some groups are small:</strong> the smallest has only {smallest.n} scoresheets.
		</li>
		<li>
			<strong>Disagreement isn’t error.</strong> Judges are meant to use their own judgement, and nothing
			here says which judge was “right”. This site doesn’t rate individual judges. Names are shown only so
			that you can check the numbers against the published scoresheets.
		</li>
	</ul>
</details>

<style>
	.limits {
		border: 1px solid var(--warn-border); border-left-width: 4px; background: var(--warn-bg);
		border-radius: 4px; padding: 0.55em 0.9em; margin: 1em 0; max-width: 72ch;
	}
	.limits summary { cursor: pointer; color: var(--warn-text); }
	.limits[open] summary { margin-bottom: 0.3em; }
	.limits ul { margin: 0.3em 0; padding-left: 1.2em; }
	.limits li + li { margin-top: 0.3em; }
</style>
