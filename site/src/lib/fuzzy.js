/**
 * Word-aware fuzzy matching, like an IDE's "go to file". Each word of the query is matched
 * separately, in any order, and all of them must match. A query word matches if its
 * characters appear in order in the text, where every jump lands at the start of a word
 * ("tss" or "tulspr" for "Tulsa Spring Swing") or stays inside the same word ("bdfst" for
 * "Budafest"). Case, accents and punctuation are ignored. Runs of characters and word
 * starts score higher; skipped characters and words cost a little.
 */

/** Letters that Unicode normalisation doesn't reduce to a plain one. */
const PLAIN = new Map(Object.entries({ ł: 'l', ø: 'o', đ: 'd', ı: 'i', æ: 'a', œ: 'o', ß: 's' }));

/** One character as it's compared: lower case, without its accent. */
const fold = (/** @type {string} */ c) => {
	const base = c.toLowerCase().normalize('NFD')[0];
	return PLAIN.get(base) ?? base;
};

const LETTER = /\p{L}/u, DIGIT = /\p{N}/u, UPPER = /\p{Lu}/u;

/**
 * A text ready to search: its letters and digits (folded), where each was in the text, the
 * word it's in, whether it starts that word, and how much a match there counts.
 * @typedef {{chars: string[], at: number[], word: number[], start: boolean[], weight: number[]}} Haystack
 */

/**
 * Prepare several fields to be searched as one text. Positions in match results are
 * [field, index] pairs. Text should be in NFC, so that each letter is one character.
 * @param {{text: string, weight?: number}[]} fields
 */
export function haystack(fields) {
	/** @type {Haystack & {field: number[]}} */
	const h = { chars: [], at: [], word: [], start: [], weight: [], field: [] };
	let word = -1;
	fields.forEach(({ text, weight = 1 }, f) => {
		let prev = '';
		for (let i = 0; i < text.length; i++) {
			const c = text[i];
			const kind = LETTER.test(c) ? 'l' : DIGIT.test(c) ? 'd' : '';
			if (kind) {
				const p = prev && (LETTER.test(prev) ? 'l' : DIGIT.test(prev) ? 'd' : '');
				// A word starts after anything else, between letters and digits, and inside "SwingOver".
				const start = p !== kind || (UPPER.test(c) && !UPPER.test(prev));
				if (start) word++;
				h.chars.push(fold(c));
				h.at.push(i);
				h.word.push(word);
				h.start.push(start);
				h.weight.push(weight);
				h.field.push(f);
			}
			prev = c;
		}
	});
	return h;
}

/** A query as a list of words, each a list of folded letters and digits. */
export const queryWords = (/** @type {string} */ q) =>
	q.normalize('NFC').split(/\s+/)
		.map((w) => [...w].filter((c) => LETTER.test(c) || DIGIT.test(c)).map(fold))
		.filter((w) => w.length);

const CHAR = 1, BONUS = 1; // A matched character, and the extra if it starts a word or continues a run.
const MID_START = -0.5;    // Starting partway through a word.
const JUMP = -0.2, SKIPPED_WORD = -0.1;
const GAP = -0.4, SKIPPED_CHAR = -0.1;
const THRESHOLD = 0.5;     // The least acceptable score, as a fraction of the best possible.

/**
 * Match one query word. Returns its score and the positions matched, or null.
 * @param {string[]} w @param {Haystack} h
 */
function matchWord(w, h) {
	const N = h.chars.length;
	// best[j]: the best score so far with this query character matched at j.
	let best = /** @type {number[]} */ ([]);
	/** @type {Int32Array[]} */
	const back = [];
	for (let i = 0; i < w.length; i++) {
		const next = new Array(N).fill(-Infinity);
		const from = new Int32Array(N).fill(-1);
		// The best place to jump from: anywhere before, and within the current word. Each is
		// kept with its skipping cost relative to a fixed origin, so one pass is enough.
		let any = -Infinity, anyAt = -1, same = -Infinity, sameAt = -1;
		let found = false;
		for (let j = 0; j < N; j++) {
			if (h.start[j]) { same = -Infinity; sameAt = -1; }
			if (h.chars[j] === w[i]) {
				const s = CHAR * h.weight[j], b = BONUS * h.weight[j];
				if (i === 0) next[j] = s + (h.start[j] ? b : MID_START);
				else {
					const take = (/** @type {number} */ v, /** @type {number} */ k) => { if (v > next[j]) { next[j] = v; from[j] = k; } };
					if (j) take(best[j - 1] + s + b, j - 1);
					if (h.start[j]) take(any + SKIPPED_WORD * (h.word[j] - 1) + JUMP + s + b, anyAt);
					else take(same + SKIPPED_CHAR * (j - 1) + GAP + s, sameAt);
				}
				if (next[j] > -Infinity) found = true;
			}
			if (i) {
				const a = best[j] - SKIPPED_WORD * h.word[j], c = best[j] - SKIPPED_CHAR * j;
				if (a > any) { any = a; anyAt = j; }
				if (c > same) { same = c; sameAt = j; }
			}
		}
		if (!found) return null;
		best = next;
		back.push(from);
	}
	let end = 0;
	for (let j = 1; j < N; j++) if (best[j] > best[end]) end = j;
	if (best[end] < THRESHOLD * w.length * (CHAR + BONUS)) return null;
	const matched = [];
	for (let i = w.length - 1, j = end; i >= 0; j = back[i][j], i--) matched.push(j);
	return { score: best[end], matched };
}

/**
 * Match every query word. Returns the total score and, for each field, the text positions
 * matched; or null if some word doesn't match.
 * @param {string[][]} words @param {ReturnType<typeof haystack>} h
 */
export function match(words, h) {
	let score = 0;
	/** @type {Set<number>[]} */
	const hits = [];
	for (const w of words) {
		const m = matchWord(w, h);
		if (!m) return null;
		score += m.score;
		for (const j of m.matched) (hits[h.field[j]] ??= new Set()).add(h.at[j]);
	}
	return { score, hits };
}

/**
 * Cut a text into runs, marking those that were matched.
 * @param {string} text @param {Set<number> | undefined} hits
 */
export function runs(text, hits) {
	/** @type {{text: string, hit: boolean}[]} */
	const out = [];
	for (let i = 0; i < text.length; i++) {
		const hit = hits?.has(i) ?? false;
		if (out.length && out[out.length - 1].hit === hit) out[out.length - 1].text += text[i];
		else out.push({ text: text[i], hit });
	}
	return out;
}
