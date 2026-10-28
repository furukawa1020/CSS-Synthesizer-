import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tools.build import ROOT, build, check_build, main


class BuildCheckTests(unittest.TestCase):
    def project(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / 'src', root / 'src')
        build(root)
        return root

    def snapshot(self, root):
        return {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                for path in (root / 'build').iterdir() if path.is_file()}

    def test_current_build_passes_without_rewriting_files(self):
        root = self.project()
        before = self.snapshot(root)
        self.assertTrue(check_build(root)['ok'])
        self.assertEqual(self.snapshot(root), before)
        self.assertEqual(list(root.glob('.build-check-*')), [])
        with patch('tools.build.ROOT', root), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--check']), 0)

    def test_changed_missing_and_extra_outputs_are_reported_without_repair(self):
        root = self.project()
        (root / 'build/engine.css').write_text('changed')
        (root / 'build/style.css').unlink()
        (root / 'build/stale.html').write_text('stale')
        before = self.snapshot(root)
        result = check_build(root)
        self.assertFalse(result['ok'])
        for word in ('不足: style.css', '余分な項目: stale.html', '一致しません: engine.css'):
            self.assertTrue(any(word in error for error in result['errors']), result['errors'])
        self.assertEqual(self.snapshot(root), before)
        with patch('tools.build.ROOT', root), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--check']), 1)

    def test_source_failure_does_not_replace_build(self):
        root = self.project()
        before = self.snapshot(root)
        with (root / 'src/page.html').open('a') as stream:
            stream.write('@@MISSING@@')
        result = check_build(root)
        self.assertFalse(result['ok'])
        self.assertIn('未解決', result['errors'][0])
        self.assertEqual(self.snapshot(root), before)
        self.assertEqual(list(root.glob('.build-check-*')), [])

    def test_missing_build_is_a_failed_check_not_a_generation_request(self):
        root = self.project()
        shutil.rmtree(root / 'build')
        self.assertFalse(check_build(root)['ok'])
        self.assertFalse((root / 'build').exists())
