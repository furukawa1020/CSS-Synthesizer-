// Development fixtures only. `npm run build` removes them from the output.
import { readFile, writeFile } from 'node:fs/promises';
const directory = new URL('../build/', import.meta.url);
const read = name => readFile(new URL(name, directory), 'utf8');
const write = (name, text) => writeFile(new URL(name, directory), text);
const html = await read('index.html');
await write('qa-square.html', html.replace('class="stage"', 'class="stage" style="inline-size:500px;block-size:500px"'));
await write('qa-frames.html', '<!doctype html><html lang="ja"><meta charset="utf-8"><title>描画領域の検証</title><iframe title="portrait" src="index.html" width="360" height="900"></iframe><iframe title="landscape" src="index.html" width="800" height="800"></iframe></html>');
await write('qa-reduced-style.css', (await read('style.css')).replaceAll('@media (prefers-reduced-motion: reduce)', '@media all'));
await write('qa-reduced-engine.css', (await read('engine.css')).replaceAll('@media (prefers-reduced-motion: reduce)', '@media all'));
await write('qa-reduced.html', html.replace('href="style.css"', 'href="qa-reduced-style.css"').replace('href="engine.css"', 'href="qa-reduced-engine.css"'));
for (const [name, k, phase, amplitude] of [['fraction',3.09,89.6,.795],['carry',3.999,359.9,.999],['upper',8,360,1]]) {
  await write(`qa-values-${name}.html`, html.replace('class="lab"', `class="lab" style="animation:none;--k-raw:${k};--phase-raw:${phase};--amplitude-raw:${amplitude}"`));
}
console.log('QA専用ページを生成しました。reduced版はCSS分岐を強制するfixtureで、実OS設定の検証ではありません。');
