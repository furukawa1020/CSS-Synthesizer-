import http.client
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from tools.build import ROOT, ASSETS, build
from tools.serve import create_server


class DevelopmentToolsTest(unittest.TestCase):
    def test_rebuild_is_deterministic_and_removes_qa(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            first = {p.name: p.read_bytes() for p in output.iterdir()}
            (output / 'qa-extra.html').write_text('QA only')
            build(root)
            self.assertEqual(set(first), set(ASSETS))
            self.assertEqual(first, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_server_confines_paths_and_keeps_csp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'build'
            output.mkdir()
            (output / 'index.html').write_text('<title>test</title>')
            (output / 'script.js').write_text('forbidden')
            (root / 'outside.html').write_text('not public')
            (output / 'escape.html').symlink_to(root / 'outside.html')
            server = create_server(output, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
            self.addCleanup(connection.close)
            for path, expected in [('/', 200), ('/script.js', 404), ('/%2e%2e/outside.html', 404), ('/escape.html', 404)]:
                connection.request('GET', path)
                response = connection.getresponse()
                self.assertEqual(response.status, expected)
                response.read()
                if expected == 200:
                    self.assertIn("script-src 'none'", response.getheader('Content-Security-Policy'))
            connection.request('HEAD', '/')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'')

    def test_repository_has_no_javascript_sources_or_node_manifest(self):
        forbidden = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'}
        excluded = {'.git', '__pycache__', 'build', 'dist', 'tmp'}
        found = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*')
                 if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts)
                 and (p.suffix.lower() in forbidden or p.name in {'package.json', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock'})]
        self.assertEqual(found, [])


if __name__ == '__main__':
    unittest.main()
