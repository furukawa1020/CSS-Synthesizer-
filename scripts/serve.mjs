import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, dirname, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../build');
const portIndex = process.argv.indexOf('--port');
const port = Number(process.env.PORT || (portIndex >= 0 ? process.argv[portIndex + 1] : 3000));
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid port');
const types = { '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8' };
const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    // Development-only environment evidence; never included in static output.
    if (pathname === '/__qa/environment') {
      response.writeHead(200, { 'Content-Type':'application/json; charset=utf-8', 'Cache-Control':'no-store' });
      response.end(JSON.stringify({ userAgent: request.headers['user-agent'] || 'unknown' }));
      return;
    }
    const path = resolve(root, `.${pathname === '/' ? '/index.html' : pathname}`);
    if (!path.startsWith(root + sep) || !types[extname(path)]) {
      response.writeHead(404).end('Not found'); return;
    }
    const data = await readFile(path);
    response.writeHead(200, {
      'Content-Type': types[extname(path)],
      'Content-Security-Policy': "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'",
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'no-store'
    });
    response.end(data);
  } catch {
    response.writeHead(404).end('Not found');
  }
});
server.listen(port, '0.0.0.0', () => console.log(`Local: http://localhost:${port}`));
