"""Local preview only. No script files, directory listing, or external dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
CSP = "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'"
TYPES = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8'}


class PreviewHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.respond(head=True)

    def do_GET(self):
        self.respond(head=False)

    def respond(self, head):
        try:
            pathname = unquote(urlsplit(self.path).path)
            if pathname == '/__qa/environment':
                data = json.dumps({'userAgent': self.headers.get('User-Agent', 'unknown')}).encode()
                content_type = 'application/json; charset=utf-8'
            else:
                root = self.server.directory.resolve()
                path = (root / ('index.html' if pathname == '/' else pathname.lstrip('/'))).resolve()
                if not path.is_relative_to(root) or not path.is_file() or path.suffix not in TYPES:
                    self.send_error(404)
                    return
                data = path.read_bytes()
                content_type = TYPES[path.suffix]
        except (ValueError, OSError):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
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
