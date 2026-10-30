"""Check shared-input scopes and audited, formula-reusing comparison output."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.assets import asset_specs
from tools.build import ROOT, build
from tools.models import load_models
from tools.comparison import comparison_filename, comparison_html, COMPARISON_COUNTS


class ComparisonParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.inputs = []; self.scopes = []; self.samples = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input': self.inputs.append(attrs)
        if tag == 'figure': self.scopes.append(attrs)
        if tag == 'i' and 'sample' in attrs.get('class', '').split(): self.samples += 1


class ComparisonTests(unittest.TestCase):
    def test_one_shared_input_and_clock_scope_and_static_model_figures(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            parser = ComparisonParser(); parser.feed((output / 'compare.html').read_text())
            self.assertEqual([f['data-static-model'] for f in parser.scopes], [model['id'] for model in load_models(root / 'src')])
            self.assertEqual(parser.samples, 96 * len(load_models(root / 'src')))
            self.assertFalse(any(i.get('name') == 'model' for i in parser.inputs))
            self.assertEqual([i['id'] for i in parser.inputs if i.get('id', '').startswith('compare-') and 'checked' in i], ['compare-lissajous', 'compare-wave'])
            self.assertIn('model-unavailable-fermat', (output / 'compare.html').read_text())
            self.assertEqual([i['id'] for i in parser.inputs if i.get('name') == 'time'], ['time-auto', 'time-play', 'time-stop'])
            self.assertIn('.comparison-example.lab', (output / 'style.css').read_text())
            self.assertIn('--clock: inherit;', (output / 'style.css').read_text())
            self.assertEqual(dict(asset_specs(root / 'src'))['compare.html'], parser.samples)
            html = (output / 'compare.html').read_text()
            for name in ('k', 'phase', 'amplitude'):
                self.assertEqual(html.count(f'class="input-band input-{name}"'), 1)
            self.assertNotIn('@@', html)

    def test_density_pages_share_definition_and_show_current_page(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            for count in COMPARISON_COUNTS:
                html = (output / comparison_filename(count)).read_text()
                parser = ComparisonParser(); parser.feed(html)
                self.assertEqual(parser.samples, count * len(load_models(root / 'src')))
                self.assertIn(f'<strong aria-current="page">{count}点</strong>', html)
                self.assertEqual(html.count('aria-current="page"'), 1)
                self.assertEqual(dict(asset_specs(root / 'src'))[comparison_filename(count)], parser.samples)
                self.assertNotIn('@@', html)
        for value in (0, 384, True, 96.0, '96'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                comparison_html('', '', [], value)
