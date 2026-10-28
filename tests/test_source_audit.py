import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from tools.source_audit import audit_source, main


class SourceAuditTests(unittest.TestCase):
    def test_source_extensions_manifests_and_dependency_directories_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('src/deep/hidden.MJS', 'tools/package.json', 'tests/test.cts',
                         'qa/source.tsx', 'package-lock.json', '.github/build.cjs'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('')
            (root / 'node_modules').mkdir()
            result = audit_source(root)
            self.assertFalse(result['ok'])
            self.assertEqual(len(result['errors']), 7)

    def test_excluded_history_outputs_and_fixture_strings_are_not_executable_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('.git/old.js', 'build/output.js', 'dist/output.js',
                         'qa/local/snapshot.js', 'docs/sample.js'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('')
            (root / 'tests').mkdir()
            (root / 'tests/test_guard.py').write_text("fixture_name = 'forbidden.js'")
            result = audit_source(root)
            self.assertTrue(result['ok'], result['errors'])
            self.assertEqual(result['files'], ['tests/test_guard.py'])

    def test_symlinks_are_not_followed_and_cli_failure_is_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tools').mkdir()
            (root / 'tools/link.py').symlink_to(root / 'outside.py')
            result = audit_source(root)
            self.assertFalse(result['ok'])
            self.assertIn('シンボリックリンク', result['errors'][0])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(root)]), 1)
