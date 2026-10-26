import { readFile, writeFile, mkdir, copyFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destination = resolve(root, 'build');
const template = await readFile(resolve(root, 'src/page.html'), 'utf8');

// Only markup is generated here. All coordinate and input calculations run in CSS.
function stops(values, initial, format) {
  return values.map((value, index) => `<span class="tick${value === initial ? ' initial' : ''}" style="--tick-index:${index}">${format(value)}</span>`).join('\n');
}

await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });
for (const count of [96, 192, 384]) {
  const tokens = {
    '@@COUNT@@': String(count),
    '@@SAMPLES@@': Array.from({ length: count }, (_, index) => `<i class="sample" data-index="${index}" style="--index-fallback:${index};--count-fallback:${count}" ></i>`).join('\n'),
    '@@K_STOPS@@': stops([1,2,3,4,5,6,7,8], 3, value => value.toFixed(2)),
    '@@PHASE_STOPS@@': stops([0,90,180,270,360], 90, value => `${value}°`),
    '@@AMPLITUDE_STOPS@@': stops(Array.from({length:16}, (_, i) => 25 + i * 5), 80, value => `${value}%`),
    '@@DENSITIES@@': [96,192,384].map(value => value === count ? `<strong aria-current="page">${value}点</strong>` : `<a href="${value === 192 ? 'index.html' : `samples-${value}.html`}">${value}点</a>`).join(' / ')
  };
  let html = template;
  for (const [token, replacement] of Object.entries(tokens)) html = html.replaceAll(token, replacement);
  if (/@@[A-Z_]+@@/.test(html)) throw new Error('未解決のテンプレートが残っています');
  await writeFile(resolve(destination, count === 192 ? 'index.html' : `samples-${count}.html`), html);
}
for (const name of ['style.css', 'engine.css']) await copyFile(resolve(root, 'src', name), resolve(destination, name));
console.log('HTML/CSSのみの検証ページを生成しました（96 / 192 / 384点）。');
