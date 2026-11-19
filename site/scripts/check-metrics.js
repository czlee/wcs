// Recomputes every metric for every scoresheet in src/lib/data/sheets.json with
// the site's JavaScript (src/lib/metrics.js) and checks it against the value
// scripts/compute_metrics.py computed. Exits non-zero on any mismatch, so CI
// won't deploy a site whose worked examples disagree with the analysis.
import { readFileSync } from 'node:fs';
import { allMetrics, TOLERANCE } from '../src/lib/metrics.js';

const sheets = JSON.parse(readFileSync(new URL('../src/lib/data/sheets.json', import.meta.url), 'utf8'));
let checked = 0, worst = 0;
const bad = [];
const check = (/** @type {string} */ what, /** @type {number} */ js, /** @type {number} */ py) => {
	const diff = Math.abs(js - py);
	worst = Math.max(worst, diff);
	checked++;
	if (!(diff <= TOLERANCE)) bad.push(`${what}: js=${js} py=${py}`);
};
for (const s of sheets) {
	const js = /** @type {Record<string, number>} */ (allMetrics(s.R));
	for (const [k, py] of Object.entries(s.py)) check(`${s.id} ${k}`, js[k], py);
	// The site shows mean pairwise ρ as the mean of the pairwise values, and the identity
	// (mW − 1)/(m − 1) that compute_metrics.py uses as an aside; check they agree.
	const m = s.R.length;
	check(`${s.id} rho identity`, js.mean_pairwise_rho, (m * js.kendall_w - 1) / (m - 1));
}
console.log(`Checked ${checked} values over ${sheets.length} scoresheets; largest difference ${worst.toExponential(2)}.`);
if (bad.length) {
	console.error(`${bad.length} mismatches (tolerance ${TOLERANCE}):\n` + bad.slice(0, 20).join('\n'));
	process.exit(1);
}
