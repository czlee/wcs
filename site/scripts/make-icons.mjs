// Renders the favicon set from the two source SVGs, into src/lib/assets/ (imported by +layout.svelte):
//   favicon.svg (flat, 16-32px) -> favicon.ico (16, 32, 48) and favicon-96x96.png
//   scripts/apple-touch-icon.svg (full-bleed, opaque, as iOS rounds the corners itself) -> apple-touch-icon.png (180)
// The ICO and PNGs use the light-theme colours (the SVG's prefers-color-scheme rules are dropped).
// Needs @resvg/resvg-js, which isn't a dependency: `npm i --no-save @resvg/resvg-js`, then `node scripts/make-icons.mjs`.
import { Resvg } from '@resvg/resvg-js';
import { readFileSync, writeFileSync } from 'node:fs';

const assets = new URL('../src/lib/assets/', import.meta.url);
const render = (svg, size) => new Resvg(svg, { fitTo: { mode: 'width', value: size } }).render().asPng();

const favicon = readFileSync(new URL('favicon.svg', assets), 'utf8').replace(/@media[^{]*\{.*\}\}/, '');
writeFileSync(new URL('favicon-96x96.png', assets), render(favicon, 96));

const sizes = [16, 32, 48];
const pngs = sizes.map((s) => render(favicon, s));
const head = Buffer.alloc(6);
head.writeUInt16LE(1, 2);
head.writeUInt16LE(sizes.length, 4);
let offset = 6 + 16 * sizes.length;
const entries = sizes.map((s, i) => {
	const e = Buffer.alloc(16);
	e[0] = e[1] = s;
	e.writeUInt16LE(1, 4);
	e.writeUInt16LE(32, 6);
	e.writeUInt32LE(pngs[i].length, 8);
	e.writeUInt32LE(offset, 12);
	offset += pngs[i].length;
	return e;
});
writeFileSync(new URL('favicon.ico', assets), Buffer.concat([head, ...entries, ...pngs]));

writeFileSync(new URL('apple-touch-icon.png', assets), render(readFileSync(new URL('apple-touch-icon.svg', import.meta.url), 'utf8'), 180));
