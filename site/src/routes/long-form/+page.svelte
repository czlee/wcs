<script>
	import FormatPage from '#lib/components/FormatPage.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>How much do WCS judges disagree? Jack & Jill finals, long-form</title>
	<meta name="description" content="How different judges’ rankings are in West Coast Swing Jack & Jill finals, by division level, with every calculation shown." />
</svelte:head>

<FormatPage {data} />
