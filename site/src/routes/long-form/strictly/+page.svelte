<script>
	import FormatPage from '#lib/components/FormatPage.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>How much do WCS judges disagree? Strictly finals, long-form</title>
	<meta name="description" content="How different judges’ rankings are in West Coast Swing Strictly finals, by division level, with every calculation shown." />
</svelte:head>

<FormatPage {data} />
