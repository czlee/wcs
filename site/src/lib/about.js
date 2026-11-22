/**
 * What the explorer says about each metric: what it measures, how to read its
 * values, and the caveats that apply to it in particular (the general ones are in
 * Limitations.svelte). Plain text: the worked example has the formulas.
 * @type {Record<string, {what: string, reading: string, caveats: string[]}>}
 */
export const ABOUT = {
	kendall_w: {
		what: 'How much the panel as a whole agrees on one order. Add up the ranks each competitor got; the more the judges agree, the further apart these rank sums are. W compares their spread with the largest spread possible.',
		reading: '0 means no common ordering at all; 1 means every judge gave the same ranking. Higher is more agreement.',
		caveats: [
			'If the judges ranked at random, W would still average 1/m for a panel of m judges, so a bigger panel gets a lower W from chance alone. W isn’t directly comparable across panel sizes; the mean pairwise Spearman ρ is the fairer of the two for that.'
		]
	},
	mean_pairwise_rho: {
		what: 'Spearman’s rank correlation between two judges’ rankings, averaged over every pair of judges on the panel. It’s based on the squared differences between the ranks the two judges gave each competitor.',
		reading: '1 means identical rankings, −1 means one is the reverse of the other, and random judging averages 0, whatever the panel size. Higher is more agreement.',
		caveats: [
			'For any one scoresheet it carries the same information as Kendall’s W (with m judges, ρ̄ = (mW − 1)/(m − 1)), rescaled so that chance is 0 for every panel size.'
		]
	},
	mean_pairwise_tau: {
		what: 'For two judges, Kendall’s τ takes every pair of competitors and asks whether both judges put the same one ahead. It’s (agreeing pairs − disagreeing pairs) ÷ all pairs, averaged over every pair of judges.',
		reading: '1 means identical rankings, −1 means one is the reverse of the other, and random judging averages 0. Higher is more agreement.',
		caveats: [
			'Random judging averages 0 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.'
		]
	},
	tau_distance: {
		what: 'The share of head-to-heads (pairs of competitors) that two judges put in opposite orders, averaged over every pair of judges. It’s (1 − τ̄)/2: the same information as the mean pairwise Kendall τ, on a scale that’s easier to read.',
		reading: '0 means identical rankings, 1 means one is the reverse of the other, and random judging averages 0.5. Lower is more agreement.',
		caveats: [
			'Random judging averages 0.5 for any field size, but in a smaller final the value varies more from one final to the next, by chance alone.'
		]
	},
	footrule_mean: {
		what: 'For two judges, add up how many places apart they put each competitor, and divide by the largest total possible (when one ranking is the reverse of the other). Averaged over every pair of judges.',
		reading: '0 means identical rankings, 1 means as different as possible. Random judging averages about 0.65 to 0.67, depending a little on the field size. Lower is more agreement.',
		caveats: []
	},
	overlap_at_3_cc: {
		what: 'Who made two judges’ top 3, whatever the order: the number of competitors in both judges’ top 3, out of 3, averaged over every pair of judges. It’s then rescaled so that 0 is what top 3s picked at random would share.',
		reading: '1 means every judge had the same top 3; 0 is chance level; below 0 is less overlap than chance. Higher is more agreement.',
		caveats: [
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.',
			'The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.'
		]
	},
	jaccard_at_3_cc: {
		what: 'Who made two judges’ top 3, whatever the order: the number of competitors in both top 3s, divided by the number in either (the Jaccard index), averaged over every pair of judges. It’s then rescaled so that 0 is what top 3s picked at random would give.',
		reading: '1 means every judge had the same top 3; 0 is chance level; below 0 is less overlap than chance. Higher is more agreement.',
		caveats: [
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.',
			'The chance correction is a naive first pass. Real judges’ top 3s aren’t random: they’re drawn towards the same strong competitors, more so in some fields than others. So it removes the chance level but not every way field size affects this metric.'
		]
	},
	overlap_at_3: {
		what: 'Who made two judges’ top 3, whatever the order: the number of competitors in both judges’ top 3, out of 3, averaged over every pair of judges.',
		reading: '1 means every judge had the same top 3; 0 means no two judges’ top 3s shared anyone. Higher is more agreement.',
		caveats: [
			'Not corrected for chance. Top 3s picked at random would share 3/n on average in a final of n, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The chance-corrected version subtracts this.',
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.'
		]
	},
	jaccard_at_3: {
		what: 'Who made two judges’ top 3, whatever the order: the number of competitors in both top 3s, divided by the number in either (the Jaccard index), averaged over every pair of judges.',
		reading: '1 means every judge had the same top 3; 0 means no two judges’ top 3s shared anyone. Higher is more agreement.',
		caveats: [
			'Not corrected for chance. Random top 3s overlap more in a smaller final, so this metric is higher in smaller finals regardless of how the judges agree, and field sizes differ between levels. The chance-corrected version subtracts this.',
			'Only finals of 6 or more are charted: in a final of 5, any two top 3s must share someone.'
		]
	},
	mean_abs_rank_dev_median: {
		what: 'For each competitor, the average distance (in places) between each judge’s rank and the median of the ranks they got. Averaged over competitors.',
		reading: '0 means every judge gave every competitor the same rank. In places, so lower is more agreement. It’s never more than the mean absolute deviation from the mean.',
		caveats: [
			'In places and not scaled to the field size: 2 places apart means more in a final of 8 than in a final of 20, and bigger finals spread further by chance. Field sizes differ between levels.'
		]
	},
	mean_abs_rank_dev_mean: {
		what: 'For each competitor, the average distance (in places) between each judge’s rank and the mean of the ranks they got. Averaged over competitors.',
		reading: '0 means every judge gave every competitor the same rank. In places, so lower is more agreement.',
		caveats: [
			'In places and not scaled to the field size: 2 places apart means more in a final of 8 than in a final of 20, and bigger finals spread further by chance. Field sizes differ between levels.'
		]
	},
	sd_rank: {
		what: 'For each competitor, the standard deviation of the ranks they got (dividing by the number of judges). Averaged over competitors. It gives more weight than the mean absolute deviations do to one judge who is far from the rest.',
		reading: '0 means every judge gave every competitor the same rank. In places, so lower is more agreement.',
		caveats: [
			'In places and not scaled to the field size: 2 places apart means more in a final of 8 than in a final of 20, and bigger finals spread further by chance. Field sizes differ between levels.'
		]
	}
};
