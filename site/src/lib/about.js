/** @typedef {{v: string, t: string, at?: number}} End `at` is where the middle one sits along the scale (0 to 1; the middle if omitted) */

/**
 * What the explorer says about each metric: one sentence on what it measures, a `scale` of its values
 * (lowest value, an optional chance level, highest value: always in numeric order, coloured by which end is better), and the caveats that apply to it in particular (the general ones are in
 * Limitations.svelte). Plain text: the worked example has the formulas.
 * @type {Record<string, {sentence: string, scale: [End, End | null, End], caveats: string[]}>}
 */
export const ABOUT = {
	kendall_w: {
		sentence: 'How spread out the competitors’ rank sums are, compared with the most they could be.',
		scale: [{v:'0',t:'max disagreement'}, {v:'1/m',t:'random ranks',at:0.2}, {v:'1',t:'fully unanimous'}],
		caveats: [
			'If the judges ranked at random, W would still average 1/m for a panel of m judges, so a bigger panel gets a lower W from chance alone. W isn’t directly comparable across panel sizes; the [[mean_pairwise_rho|mean pairwise Spearman ρ]] is the fairer of the two for that.'
		]
	},
	mean_pairwise_rho: {
		sentence: 'How closely pairs of judges’ rankings track each other, from the squared gaps between their ranks, averaged over every pair.',
		scale: [{v:'−1/(m−1)',t:'max disagreement'}, {v:'0',t:'random ranks',at:0.2}, {v:'1',t:'fully unanimous'}],
		caveats: [
			'For any one scoresheet it carries the same information as [[kendall_w|Kendall’s W]] (with m judges, ρ̄ = (mW − 1)/(m − 1)), rescaled so that chance is 0 for every panel size.'
		]
	},
	tau_distance: {
		sentence: 'The share of head-to-heads (pairs of competitors) that two judges put in opposite orders, averaged over every pair of judges.',
		scale: [{v:'0',t:'fully unanimous'}, {v:'0.5',t:'random ranks',at:0.62}, {v:'(m+1)/(2m)',t:'max disagreement'}],
		caveats: [
			'Random judging averages 0.5 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.'
		]
	},
	mean_pairwise_tau: {
		sentence: 'Agreeing minus disagreeing head-to-heads between two judges, as a share of all of them, averaged over every pair of judges.',
		scale: [{v:'−1/m',t:'max disagreement'}, {v:'0',t:'random ranks',at:0.2}, {v:'1',t:'fully unanimous'}],
		caveats: [
			'Random judging averages 0 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.'
		]
	},
	footrule_mean: {
		sentence: 'How many places apart two judges put each competitor, added up, as a share of the most possible, averaged over every pair.',
		scale: [{v:'0',t:'fully unanimous'}, {v:'≈0.66',t:'random ranks',at:0.66}, {v:'1',t:'max disagreement'}],
		caveats: []
	},
	overlap_at_3_cc: {
		sentence: 'How many of the same competitors two judges put in their top 3, averaged over every pair, with chance-level overlap set to 0.',
		scale: [{v:'below 0',t:'less overlap than random'}, {v:'0',t:'random top 3s',at:0.25}, {v:'1',t:'same top 3s'}],
		caveats: [
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.',
			'The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.'
		]
	},
	jaccard_at_3_cc: {
		sentence: 'The share of competitors in either judge’s top 3 that are in both, averaged over every pair, with chance-level overlap set to 0.',
		scale: [{v:'below 0',t:'less overlap than random'}, {v:'0',t:'random top 3s',at:0.25}, {v:'1',t:'same top 3s'}],
		caveats: [
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.',
			'The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.'
		]
	},
	overlap_at_3: {
		sentence: 'How many of the same competitors two judges put in their top 3, averaged over every pair of judges.',
		scale: [{v:'0',t:'no overlap at all'}, {v:'3/n',t:'random top 3s',at:0.25}, {v:'1',t:'same top 3s'}],
		caveats: [
			'Not corrected for chance. Top 3s picked at random would share 3/n on average in a final of n, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The [[overlap_at_3_cc|chance-corrected version]] subtracts this.',
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.'
		]
	},
	jaccard_at_3: {
		sentence: 'The share of competitors in either judge’s top 3 that are in both, averaged over every pair of judges.',
		scale: [{v:'0',t:'no overlap at all'}, null, {v:'1',t:'same top 3s'}],
		caveats: [
			'Not corrected for chance. Random top 3s overlap more in a smaller final, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The [[jaccard_at_3_cc|chance-corrected version]] subtracts this.',
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.'
		]
	},
	mean_abs_rank_dev_median_norm: {
		sentence: 'How far each judge’s rank for a competitor is from the median, averaged over judges and competitors and scaled by the field size.',
		scale: [{v:'0',t:'fully unanimous'}, null, {v:'1',t:'panel split in two'}],
		caveats: [
			'Normalised for field size only roughly, by dividing by n/4, the most the average can be: it’s what the average is when half the panel ranks in order and half in exact reverse. Some panels (an odd number of finalists or of judges) can’t quite reach it, so a maximally split panel reads a little under 1 there. That removes the main effect of field size, but random rankings don’t land at the same value for every field and panel size, so some of it remains. A proper chance correction is planned.'
		]
	},
	sd_rank_norm: {
		sentence: 'How much the judges’ ranks for each competitor vary, averaged over competitors and scaled by the field size.',
		scale: [{v:'0',t:'fully unanimous'}, null, {v:'1',t:'max disagreement'}],
		caveats: [
			'Normalised for field size only roughly. That removes the main effect of field size, but random rankings don’t land at the same value for every panel size (a bit under 1, and further under for small panels), and a panel of two judges can’t reach 1. A proper chance correction is planned.'
		]
	}
};
