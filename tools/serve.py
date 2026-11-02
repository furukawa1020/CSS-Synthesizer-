"""Local preview only. No script files, directory listing, or external dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CSP = "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'"
TYPES = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8'}


class PreviewHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_HEAD(self):
        self.respond(head=True)

    def do_GET(self):
        self.respond(head=False)

    def respond(self, head):
        try:
            hosts = self.headers.get_all('Host', [])
            authority = urlsplit('//' + hosts[0]) if len(hosts) == 1 else None
            if (authority is None or authority.hostname not in ('localhost', '127.0.0.1', '::1')
                    or authority.username is not None or authority.password is not None
                    or authority.path or authority.query or authority.fragment
                    or (authority.port is not None and authority.port != self.server.server_port)):
                self.send_error(403)
                return
        except ValueError:
            self.send_error(403)
            return
        try:
            url = urlsplit(self.path)
            if url.scheme or url.netloc:
                raise ValueError('ローカルのパスにしてください')
            pathname = unquote(url.path, errors='strict')
            if pathname == '/__qa/environment':
                data = json.dumps({'userAgent': self.headers.get('User-Agent', 'unknown')}).encode()
                content_type = 'application/json; charset=utf-8'
            else:
                root = self.server.directory.resolve()
                name = 'index.html' if pathname == '/' else pathname.removeprefix('/')
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.(?:html|css)', name):
                    raise ValueError('直下のHTML/CSSだけを配信します')
                path = root / name
                if path.is_symlink():
                    raise ValueError('シンボリックリンクは配信しません')
                if not path.is_relative_to(root) or not path.is_file() or path.suffix not in TYPES:
                    self.send_error(404)
                    return
                data = path.read_bytes()
                content_type = TYPES[path.suffix]
        except (ValueError, OSError, UnicodeError):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if not head:
            self.wfile.write(data)


def create_server(directory=ROOT / 'build', host='127.0.0.1', port=3000):
    server = ThreadingHTTPServer((host, port), PreviewHandler)
    server.directory = Path(directory)
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTML/CSSのローカル確認')
    parser.add_argument('--port', type=int, default=3000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('portは1〜65535です')
    server = create_server(port=args.port)
    print(f'Local: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
