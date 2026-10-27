import tempfile
from pathlib import Path
import unittest
from tools.source import expand_fragments, compose_css


class SourceTests(unittest.TestCase):
    def test_nested_fragments_keep_runtime_tokens_for_the_builder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'fragments').mkdir()
            (root / 'fragments/a.html').write_text('<p>@@FRAGMENT:b@@</p>')
            (root / 'fragments/b.html').write_text('@@COUNT@@')
            self.assertEqual(expand_fragments('@@FRAGMENT:a@@', root), '<p>@@COUNT@@</p>')

    def test_missing_cycles_traversal_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'fragments').mkdir()
            (root / 'fragments/a.html').write_text('@@FRAGMENT:a@@')
            (root / 'fragments/link.html').symlink_to(root / 'fragments/a.html')
            for name in ('missing', 'a', '../a', 'link', ''):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    expand_fragments(f'@@FRAGMENT:{name}@@', root)

    def test_fragment_directory_symlink_and_incomplete_tokens_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'outside').mkdir()
            (root / 'outside/leak.html').write_text('outside')
            (root / 'fragments').symlink_to(root / 'outside', target_is_directory=True)
            with self.assertRaises(ValueError):
                expand_fragments('@@FRAGMENT:leak@@', root)
            (root / 'fragments').unlink()
            for token in ('@@FRAGMENT:missing', '@@FRAGMENT:x@'):
                with self.subTest(token=token), self.assertRaises(ValueError):
                    expand_fragments(token, root)

    def test_css_extensions_have_deterministic_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'style.css').write_text('base')
            (root / 'styles').mkdir()
            (root / 'styles/b.css').write_text('b')
            (root / 'styles/a.css').write_text('a')
            self.assertEqual(compose_css(root, 'style.css'), 'base\na\nb')
