import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { auditHTML, auditCSS } from '../scripts/audit.mjs';

const points = count => `<div class="plot">${'<i class="sample"></i>'.repeat(count)}</div>`;

test('ローカルCSS・ネイティブ要素・外部の説明リンク・エスケープ済みコードは許可する', () => {
  const html = `<!doctype html><html lang="ja"><head>
    <meta http-equiv="Content-Security-Policy" content="script-src 'none'">
    <link rel="stylesheet" href="style.css"><link rel="icon" href="data:,">
    </head><body><input type="radio" name="model"><details><summary>式</summary>
    <code>&lt;script&gt; は使わない</code><a href="https://developer.mozilla.org/">資料</a>
    </details><!-- <script src="https://example.invalid/unused.js"></script> -->
    ${points(2)}<p title="k > 1">値</p></body></html>`;
  assert.deepEqual(auditHTML(html, { samples: 2 }), { ok: true, errors: [], sampleCount: 2 });
});

test('大文字小文字や属性の有無に関係なく実行・別描画要素を検出する', () => {
  for (const html of ['<ScRiPt type="module"></ScRiPt>', '<script type="application/json">{}</script>', '<canvas></canvas>', '<svg viewBox="0 0 1 1"></svg>']) {
    assert.equal(auditHTML(html).ok, false, html);
  }
});

test('引用符付き・引用符なし・大文字のイベント属性を検出する', () => {
  for (const html of ['<button onclick="x()">', '<input ONFOCUS=x()>', '<img onerror = \'x()\' src="local.png">']) {
    assert.match(auditHTML(html).errors.join('\n'), /イベントハンドラ属性/);
  }
  assert.equal(auditHTML('<p data-on="value" class="only">説明</p>').ok, true);
});

test('文字参照やASCII空白で隠されたjavascript URLも拒否する', () => {
  for (const value of ['javascript:alert(1)', 'JaVaScRiPt:alert(1)', '&#106;avascript&#58;alert(1)', 'java&#x09;script&colon;alert(1)', '&#x6a;avascript:alert(1)']) {
    assert.match(auditHTML(`<a href="${value}">移動</a>`).errors.join('\n'), /javascript:/, value);
  }
});

test('実行時に取得する外部リソースを検出し、通常のリンクと区別する', () => {
  for (const html of [
    '<link rel="stylesheet" href="https://example.invalid/main.css">',
    '<img src="//example.invalid/a.png">',
    '<source srcset="local.png 1x, https://example.invalid/a.png 2x">',
    '<iframe src="https://example.invalid/"></iframe>',
    '<base href="https://example.invalid/"><link rel="stylesheet" href="relative.css">',
    '<form action="https://example.invalid/submit"></form>',
    '<style>@import "https://example.invalid/font.css";</style>',
    '<p style="background:url(https://example.invalid/a.png)">',
    '<a href="./" ping="https://example.invalid/track">移動</a>',
    '<img src="data:image/svg+xml,&lt;svg/&gt;">',
  ]) assert.equal(auditHTML(html).ok, false, html);
  assert.equal(auditHTML('<link rel="canonical" href="https://example.invalid/"><p style="background:url(local.png)">').ok, true);
});

test('実際のi.sampleのみを数え、任意の期待数と照合する', () => {
  const html = `${points(3)}<i class="sample-extra"></i><span class="sample"></span><!-- <i class="sample"></i> -->`;
  assert.equal(auditHTML(html, { samples: 3 }).ok, true);
  assert.equal(auditHTML(html).sampleCount, 3);
  assert.match(auditHTML(html, { samples: 4 }).errors.join('\n'), /expected 4, got 3/);
  assert.throws(() => auditHTML(html, { samples: 0 }), TypeError);
});

test('生成時のトークン残存を検出するが、通常のCSS値は許可する', () => {
  for (const token of ['{{SAMPLES}}', '__SAMPLE_POINTS__', '@@SAMPLES@@', '<!--POINTS-->']) {
    assert.match(auditHTML(token).errors.join('\n'), /テンプレートトークン/);
  }
  assert.equal(auditHTML('<style>.sample{left:calc(50% + var(--x) * 1px)}</style>').ok, true);
});

test('CSSファイルの外部URLとimportを検出し、ローカル画像とコメントは許可する', () => {
  for (const css of [
    '@import "https://example.invalid/font.css";',
    '@import url(//example.invalid/theme.css);',
    '@font-face{font-family:Test;src:url("https://example.invalid/font.woff2")}',
    '.plot{background-image:url(https://example.invalid/a.png)}',
  ]) assert.match(auditCSS(css).errors.join('\n'), /外部CSSリソース/, css);
  assert.deepEqual(auditCSS('/* @import "https://example.invalid/unused.css"; */ .plot{background:url(local.png)}'), { ok: true, errors: [] });
  assert.throws(() => auditCSS(null), TypeError);
});

test('CLIは3ページと2スタイルを検査し、不正な成果物と欠落ページを失敗にする', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'css-synth-audit-'));
  const cli = fileURLToPath(new URL('../scripts/audit.mjs', import.meta.url));
  try {
    for (const [name, count] of [['index.html', 192], ['samples-96.html', 96], ['samples-384.html', 384]]) {
      await writeFile(join(directory, name), points(count));
    }
    await writeFile(join(directory, 'style.css'), 'body{color:#222}');
    await writeFile(join(directory, 'engine.css'), '.sample{left:50%;top:50%}');
    const good = spawnSync(process.execPath, [cli, directory], { encoding: 'utf8' });
    assert.equal(good.status, 0, good.stderr);
    assert.equal(good.stdout.match(/PASS /g)?.length, 5);
    await writeFile(join(directory, 'index.html'), `${points(192)}<script></script>`);
    await writeFile(join(directory, 'style.css'), '@import "https://example.invalid/theme.css";');
    await rm(join(directory, 'samples-96.html'));
    const bad = spawnSync(process.execPath, [cli, directory], { encoding: 'utf8' });
    assert.equal(bad.status, 1);
    assert.match(bad.stderr, /FAIL index.html/);
    assert.match(bad.stderr, /FAIL samples-96.html/);
    assert.match(bad.stderr, /FAIL style.css/);
    assert.match(bad.stdout, /PASS samples-384.html/);
    assert.match(bad.stdout, /PASS engine.css/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
