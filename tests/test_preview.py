import contextlib
import http.client
import io
from pathlib import Path
import tempfile
import threading
import unittest
from tools.serve import create_server

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'index.html').write_text('<title>ok</title>')

    def start(self, **kw):
        server = create_server(self.root, port=0, **kw)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server

    def request(self, server, path='/', method='GET', headers=None):
        con = http.client.HTTPConnection('127.0.0.1', server.server_port)
        try:
            con.request(method, path, headers=headers or {})
            res = con.getresponse()
            return res.status, dict(res.getheaders()), res.read()
        finally:
            con.close()

    def test_only_flat_regular_assets_are_served(self):
        (self.root / 'nested').mkdir()
        (self.root / 'nested/page.html').write_text('secret')
        (self.root / 'local.html').symlink_to(self.root / 'index.html')
        (self.root / '%2e.html').write_text('double encoded')
        server = self.start()
        for path in ('/nested/page.html', '/nested%2fpage.html', '/local.html', '/%252e.html', '/%00.html', '/%ff.html', '//evil.test/index.html'):
            with self.subTest(path=path): self.assertEqual(self.request(server, path)[0], 404)
        self.assertEqual(self.request(server, '/index.html?cache=1')[0], 200)
