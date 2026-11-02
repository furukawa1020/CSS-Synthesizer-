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

    def test_security_headers_cover_success_and_errors(self):
        server = self.start()
        for method, path, code in [('GET','/',200),('GET','/missing',404),('POST','/',501),('HEAD','/missing',404)]:
            status, headers, body = self.request(server, path, method)
            self.assertEqual(status, code)
            self.assertIn("script-src 'none'", headers['Content-Security-Policy'])
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(headers['Cache-Control'], 'no-store')
            if method == 'HEAD': self.assertEqual(body, b'')

    def test_host_header_must_name_local_preview(self):
        server = self.start()
        for host in ('evil.test', 'localhost.evil.test', 'localhost@evil.test', 'evil.test@localhost', 'localhost/path', 'localhost:wrong', 'localhost:1'):
            self.assertEqual(self.request(server, headers={'Host':host})[0], 403, host)
        for host in ('localhost', f'127.0.0.1:{server.server_port}', f'localhost:{server.server_port}'):
            self.assertEqual(self.request(server, headers={'Host':host})[0], 200)

    def test_zero_port_allocates_a_working_listener(self):
        server = self.start()
        self.assertGreater(server.server_port, 0)
        self.assertEqual(self.request(server)[0], 200)

    def test_invalid_directory_fails_before_binding(self):
        with self.assertRaises(ValueError): create_server(self.root/'missing', port=0)
        alias = self.root/'alias'; alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): create_server(alias, port=0)
        with self.assertRaises(ValueError): create_server(self.root, host='0.0.0.0', port=0)
