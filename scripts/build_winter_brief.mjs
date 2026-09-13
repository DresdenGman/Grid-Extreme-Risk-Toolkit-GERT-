/** Rebuild a source-derived standalone graphic. No invented or smoothed values. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import sharp from 'sharp';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = readFileSync(path.join(root, 'public/data/historical-cases.json'));
const sha = createHash('sha256').update(input).digest('hex');
if (sha !== 'f403890ad50a654f85584e03642267d1a06bafb25bf4799346bbf87c4999181b') throw new Error('Review the dataset change before rebuilding.');
const bundle = JSON.parse(input);
const example = bundle.cases.find((item) => item.id === 'winter-2021');
if (example.hours.length !== 72) throw new Error('Expected 72 hourly observations.');
example.hours.forEach((hour, i) => {
  if (!Number.isFinite(hour.load_mw) || hour.load_mw < 0 || hour.load_mw > 80000) throw new Error('Plot bounds need review.');
  if (i && Date.parse(hour.timestamp) - Date.parse(example.hours[i - 1].timestamp) !== 3600000) throw new Error('Non-contiguous observations.');
});
const out = path.join(root, 'public/briefs');
mkdirSync(out, { recursive: true });
const x = (index) => 136 + index / 71 * 1328;
const y = (mw) => 816 - mw / 80000 * 404;
const polyline = example.hours.map((hour, i) => `${x(i).toFixed(2)},${y(hour.load_mw).toFixed(2)}`).join(' ');
const ticks = [0, 20000, 40000, 60000, 80000].map((value) => `<line x1="136" x2="1464" y1="${y(value)}" y2="${y(value)}" stroke="#d1d0c9"/><text x="112" y="${y(value) + 8}" text-anchor="end" font-size="25">${value / 1000}</text>`).join('');
const dateTicks = [[0, 'Feb 14 · 00h'], [24, 'Feb 15 · 00h'], [48, 'Feb 16 · 00h'], [71, 'Feb 16 · 23h']].map(([index, label]) => `<text x="${x(index)}" y="858" text-anchor="${index === 0 ? 'start' : index === 71 ? 'end' : 'middle'}" font-size="24">${label}</text>`).join('');
const eventX = x(25 + 25 / 60);
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200" role="img" aria-labelledby="title desc">
<title id="title">A falling load curve isn't a safety signal</title>
<desc id="desc">72 hourly ERCOT native-load observations, February 14 to 16, 2021. The vertical scale is zero to 80 gigawatts. The curve does not measure unmet demand. A dashed reference marks the reported start of rotating outages, not the duration or quantity of lost load.</desc>
<rect width="1600" height="1200" fill="#f7f6f2"/>
<rect width="1600" height="14" fill="#b73700"/>
<g fill="#171717" font-family="Arial, Helvetica, sans-serif">
<text x="80" y="82" font-size="26" font-weight="700" letter-spacing="3">GERT / GRID NOTES 01</text>
<text x="80" y="174" font-size="66" font-weight="700">A falling load curve</text>
<text x="80" y="251" font-size="66" font-weight="700">isn't a safety signal.</text>
<text x="80" y="306" font-size="29" fill="#514e48">Recorded electricity use can fall when customers lose power.</text>
<text x="80" y="365" font-size="24" font-weight="700">ERCOT native load · February 14–16, 2021 · hourly interval starts (CST)</text>
<text x="80" y="397" font-size="22" fill="#514e48">Recorded load (GW) · 72 observations · zero-based scale</text>
${ticks}<line x1="136" y1="412" x2="136" y2="816" stroke="#171717"/><line x1="136" y1="816" x2="1464" y2="816" stroke="#171717"/>
<line x1="${eventX}" y1="412" x2="${eventX}" y2="816" stroke="#514e48" stroke-width="2" stroke-dasharray="8 7"/>
<polyline points="${polyline}" fill="none" stroke="#b73700" stroke-width="5" stroke-linejoin="round"/>
<rect x="${eventX + 20}" y="431" width="595" height="76" fill="#f7f6f2"/>
<text x="${eventX + 34}" y="459" font-size="23">Rotating outages began Feb 15, 01:25 CST</text>
<text x="${eventX + 34}" y="490" font-size="22" fill="#514e48">Context: ERCOT's February 15 news release</text>
${dateTicks}
<rect x="80" y="902" width="1440" height="142" fill="#ebe3cf"/>
<text x="108" y="944" font-size="29" font-weight="700">What is missing from the curve?</text>
<text x="108" y="987" font-size="26">The electricity people would have used without interruptions.</text>
<text x="108" y="1024" font-size="23">Do not treat the drop as measured outage losses, energy savings, or improved reliability.</text>
<text x="80" y="1090" font-size="25" font-weight="700">Try the exercise &amp; inspect sources: gert-d.vercel.app/briefs/winter-load</text>
<text x="80" y="1135" font-size="21" fill="#514e48">Data: ERCOT Native Load 2021 archive. Context and full hourly table linked with the exercise.</text>
<text x="80" y="1170" font-size="20" fill="#514e48">GERT · Dresden Goehner · Historical education, not a live forecast · Original material: repository MIT license</text>
</g></svg>`;
writeFileSync(path.join(out, 'winter-load.svg'), svg);
await sharp(Buffer.from(svg)).png().toFile(path.join(out, 'winter-load.png'));
writeFileSync(path.join(out, 'winter-load-figure-data.json'), JSON.stringify({
  figure_version: 'winter-load-brief-v1', dataset_sha256: sha,
  source_url: example.source_url, source_archive_sha256: example.source_archive_sha256,
  context_url: 'https://www.ercot.com/news/release?id=9c552983-008a-3906-8066-8b76315ed3e7',
  event_reference: '2021-02-15T01:25:00-06:00',
  event_reference_meaning: 'Reported onset only; not a reconstructed load-shed quantity or duration.',
  axis: { y_min_gw: 0, y_max_gw: 80, x_first: example.hours[0].timestamp, x_last: example.hours.at(-1).timestamp },
  hours: example.hours,
}, null, 2) + '\n');
console.log(`Generated 1600 × 1200 PNG and SVG from ${example.hours.length} observed rows; source ${sha}.`);
