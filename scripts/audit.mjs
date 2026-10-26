#!/usr/bin/env node
/**
 * Static guard for this project's generated spike pages, not a general HTML
 * sanitizer or a replacement for browser/CSP verification. It deliberately
 * rejects features that this HTML/CSS-only experiment does not need.
 */
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const resourceAttributes = new Map([
  ['img', new Set(['src', 'srcset'])],
  ['source', new Set(['src', 'srcset'])],
  ['audio', new Set(['src'])],
  ['video', new Set(['src', 'poster'])],
  ['iframe', new Set(['src'])],
  ['embed', new Set(['src'])],
  ['object', new Set(['data'])],
  ['input', new Set(['src', 'formaction'])],
  ['button', new Set(['formaction'])],
  ['form', new Set(['action'])],
  ['base', new Set(['href'])],
]);
const fetchingLinkRels = new Set([
  'stylesheet', 'icon', 'preload', 'prefetch', 'modulepreload', 'manifest',
  'preconnect', 'dns-prefetch', 'apple-touch-icon',
]);
const urlAttributes = new Set([
  'href', 'src', 'srcset', 'action', 'formaction', 'poster', 'data',
  'xlink:href', 'ping',
]);

// Only character references relevant to URL/attribute checks are decoded.
// Unknown named entities remain literal; this is not a browser HTML parser.
function decodeReferences(value) {
  return value.replace(/&#(?:x([0-9a-f]+)|([0-9]+));?|&(colon|tab|newline|amp|quot|apos);/gi,
    (match, hex, decimal, named) => {
      if (hex || decimal) {
        const point = Number.parseInt(hex || decimal, hex ? 16 : 10);
        return point > 0 && point <= 0x10ffff ? String.fromCodePoint(point) : '\ufffd';
      }
      return { colon: ':', tab: '\t', newline: '\n', amp: '&', quot: '"', apos: "'" }[named.toLowerCase()];
    });
}

function compactURL(value) {
  return decodeReferences(value).replace(/[\u0000-\u0020\u007f]/g, '');
}

function externalResource(value) {
  const url = compactURL(value);
  if (/^data:/i.test(url)) return false;
  return url.startsWith('//') || /^[a-z][a-z0-9+.-]*:/i.test(url);
}

function resourceCandidates(value, attribute) {
  if (attribute === 'srcset' || attribute === 'ping') {
    // Generated pages do not use data-URL srcsets. Splitting here also detects
    // a remote candidate following a local image and its width descriptor.
    return decodeReferences(value).split(/[\s,]+/).filter(Boolean);
  }
  return [value];
}

function inspectCSS(css, report) {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const urls = /url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)|@import\s+(?:"([^"]*)"|'([^']*)')/gi;
  for (const match of withoutComments.matchAll(urls)) {
    const value = match.slice(1).find(part => part !== undefined) ?? '';
    if (externalResource(value)) report(`外部CSSリソース: ${value.trim()}`);
    if (/^javascript:/i.test(compactURL(value))) report('CSS内のjavascript: URL');
    if (/^data:image\/svg\+xml/i.test(compactURL(value))) report('CSS内のSVGデータURL');
  }
}

/** Inspect a generated stylesheet. This is the same project guard as auditHTML. */
export function auditCSS(css) {
  if (typeof css !== 'string') throw new TypeError('css must be a string');
  const errors = [];
  inspectCSS(css, message => errors.push(message));
  return { ok: errors.length === 0, errors: [...new Set(errors)] };
}

/**
 * @param {string} html Generated HTML source, before any preview injection.
 * @param {{samples?: number}} [options]
 * @returns {{ok: boolean, errors: string[], sampleCount: number}}
 */
export function auditHTML(html, { samples } = {}) {
  if (typeof html !== 'string') throw new TypeError('html must be a string');
  if (samples !== undefined && (!Number.isInteger(samples) || samples < 1)) {
    throw new TypeError('samples must be a positive integer');
  }
  const errors = [];
  const report = message => errors.push(message);
  if (/\{\{[^{}]+\}\}|__[A-Z][A-Z0-9_]*__|@@[A-Z][A-Z0-9_]*@@|<!--\s*(?:SAMPLES|POINTS|[A-Z]+_STEPS)\s*-->/i.test(html)) {
    report('未解決のテンプレートトークン');
  }

  const source = html.replace(/<!--[\s\S]*?-->/g, '');
  let sampleCount = 0;
  // Quoted > characters stay inside their attribute, rather than ending a tag.
  const startTags = /<\s*([a-z][\w:-]*)\b((?:"[^"]*"|'[^']*'|[^'">])*)>/gi;
  for (const tagMatch of source.matchAll(startTags)) {
    const tag = tagMatch[1].toLowerCase();
    if (['script', 'canvas', 'svg'].includes(tag)) report(`禁止された要素: <${tag}>`);
    const attrs = [];
    const attributePattern = /([^\s=/'"<>`]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
    for (const attr of tagMatch[2].matchAll(attributePattern)) {
      attrs.push([attr[1].toLowerCase(), attr[2] ?? attr[3] ?? attr[4] ?? '']);
    }
    const first = name => attrs.find(([key]) => key === name)?.[1] ?? '';
    if (tag === 'i' && decodeReferences(first('class')).split(/\s+/).includes('sample')) sampleCount++;
    const rels = first('rel').toLowerCase().split(/\s+/);

    for (const [name, value] of attrs) {
      if (/^on/i.test(name)) report(`イベントハンドラ属性: <${tag} ${name}>`);
      if (urlAttributes.has(name) && /^javascript:/i.test(compactURL(value))) {
        report(`javascript: URL: <${tag} ${name}>`);
      }
      if (urlAttributes.has(name) && /^data:image\/svg\+xml/i.test(compactURL(value))) {
        report(`SVGデータURL: <${tag} ${name}>`);
      }
      const isResource = resourceAttributes.get(tag)?.has(name)
        || (tag === 'link' && name === 'href' && rels.some(rel => fetchingLinkRels.has(rel)))
        || (tag === 'a' && name === 'ping');
      if (isResource && resourceCandidates(value, name).some(externalResource)) {
        report(`外部実行時リソース: <${tag} ${name}>`);
      }
      if (name === 'style') inspectCSS(decodeReferences(value), report);
      if (tag === 'iframe' && name === 'srcdoc') report('このスパイクではiframe srcdocを使用しない');
    }
    if (tag === 'meta' && first('http-equiv').toLowerCase() === 'refresh') {
      report('このスパイクではmeta refreshを使用しない');
    }
  }
  for (const style of source.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style\s*>/gi)) {
    inspectCSS(style[1], report);
  }
  if (samples !== undefined && sampleCount !== samples) {
    report(`サンプル数が不一致: expected ${samples}, got ${sampleCount}`);
  }
  return { ok: errors.length === 0, errors: [...new Set(errors)], sampleCount };
}

async function runCLI() {
  const directory = resolve(process.argv[2] ?? fileURLToPath(new URL('../build/', import.meta.url)));
  const pages = [['index.html', 192], ['samples-96.html', 96], ['samples-384.html', 384]];
  for (const [file, samples] of pages) {
    try {
      const result = auditHTML(await readFile(resolve(directory, file), 'utf8'), { samples });
      if (result.ok) {
        console.log(`PASS ${file}: ${result.sampleCount} samples, HTML/CSS静的ガード`);
      } else {
        process.exitCode = 1;
        console.error(`FAIL ${file}\n${result.errors.map(error => `  - ${error}`).join('\n')}`);
      }
    } catch (error) {
      process.exitCode = 1;
      console.error(`FAIL ${file}: ${error.message}`);
    }
  }
  for (const file of ['style.css', 'engine.css']) {
    try {
      const result = auditCSS(await readFile(resolve(directory, file), 'utf8'));
      if (result.ok) {
        console.log(`PASS ${file}: CSS外部リソース静的ガード`);
      } else {
        process.exitCode = 1;
        console.error(`FAIL ${file}\n${result.errors.map(error => `  - ${error}`).join('\n')}`);
      }
    } catch (error) {
      process.exitCode = 1;
      console.error(`FAIL ${file}: ${error.message}`);
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await runCLI();
}
