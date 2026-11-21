<script>
	import ExplorePage from '#lib/components/ExplorePage.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Explore: Jack & Jill finals · WCS judge divergence</title>
	<meta name="description" content="How different judges’ rankings are in West Coast Swing Jack & Jill finals, one metric at a time." />
</svelte:head>

<ExplorePage {data} />
