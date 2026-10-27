"""Candidate generation failures must not erase the last usable build."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.build import ROOT, build


class BuildPreservationTests(unittest.TestCase):
    def project(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / 'src', root / 'src')
        output = build(root)
        return root, {path.name: path.read_bytes() for path in output.iterdir()}

    def assert_previous(self, root, previous):
        self.assertEqual(previous, {path.name: path.read_bytes() for path in (root / 'build').iterdir()})
        self.assertEqual(list(root.glob('.build-candidate-*')), [])
        self.assertEqual(list(root.glob('.build-previous-*')), [])

    def test_unresolved_template_keeps_previous_files(self):
        root, previous = self.project()
        with (root / 'src/page.html').open('a') as stream:
            stream.write('@@UNKNOWN@@')
        with self.assertRaisesRegex(ValueError, '未解決'):
            build(root)
        self.assert_previous(root, previous)

    def test_missing_css_and_audit_failure_keep_previous_files(self):
        for failure in ('missing', 'forbidden'):
            with self.subTest(failure=failure):
                root, previous = self.project()
                css = root / 'src/engine.css'
                if failure == 'missing':
                    css.unlink()
                else:
                    css.write_text('@import "https://example.invalid/remote.css";')
                with self.assertRaises((OSError, ValueError)):
                    build(root)
                self.assert_previous(root, previous)

    def test_install_error_restores_previous_directory(self):
        root, previous = self.project()
        real_rename = Path.rename
        def rename(path, target):
            if path.name == 'build' and path.parent.name.startswith('.build-candidate-'):
                raise OSError('simulated install failure')
            return real_rename(path, target)
        with patch.object(Path, 'rename', rename):
            with self.assertRaisesRegex(OSError, 'simulated'):
                build(root)
        self.assert_previous(root, previous)

    def test_success_replaces_previous_and_removes_stale_qa(self):
        root, previous = self.project()
        (root / 'build/qa-old.html').write_text('old QA')
        with (root / 'src/style.css').open('a') as stream:
            stream.write('\nbody { outline: 0; }')
        build(root)
        self.assertFalse((root / 'build/qa-old.html').exists())
        self.assertNotEqual((root / 'build/style.css').read_bytes(), previous['style.css'])
        self.assertEqual(list(root.glob('.build-candidate-*')), [])
        self.assertEqual(list(root.glob('.build-previous-*')), [])
