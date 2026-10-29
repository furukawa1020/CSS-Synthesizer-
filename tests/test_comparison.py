"""Check shared-input scopes and audited, formula-reusing comparison output."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.assets import asset_specs
from tools.build import ROOT, build


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
            self.assertEqual([f['data-static-model'] for f in parser.scopes], ['lissajous', 'wave'])
            self.assertEqual(parser.samples, 192)
            self.assertFalse(any(i.get('name') == 'model' for i in parser.inputs))
            self.assertEqual([i['id'] for i in parser.inputs if i.get('name') == 'time'], ['time-auto', 'time-play', 'time-stop'])
            self.assertIn('.comparison-example.lab', (output / 'style.css').read_text())
            self.assertIn('--clock: inherit;', (output / 'style.css').read_text())
            self.assertEqual(dict(asset_specs(root / 'src'))['compare.html'], parser.samples)
            html = (output / 'compare.html').read_text()
            for name in ('k', 'phase', 'amplitude'):
                self.assertEqual(html.count(f'class="input-band input-{name}"'), 1)
            self.assertNotIn('@@', html)
