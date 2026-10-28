"""Static preview data and runtime engine sharing, without browser claims."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.assets import asset_specs
from tools.audit import audit_html
from tools.build import ROOT, build
from tools.gallery import static_model_selectors
from tools.presets import load_presets


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.examples = []
        self.samples = 0
        self.links = []
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'figure':
            self.examples.append(attrs)
        if tag == 'i' and 'sample' in attrs.get('class', '').split():
            self.samples += 1
        if tag == 'a':
            self.links.append(attrs.get('href'))
        if tag == 'input':
            self.inputs.append(attrs)


class GalleryTests(unittest.TestCase):
    def test_every_registry_entry_has_one_96_point_static_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            text = (output / 'gallery.html').read_text()
            presets = load_presets(root / 'src')
            parser = GalleryParser()
            parser.feed(text)
            self.assertEqual(len(parser.examples), len(presets))
            self.assertEqual(parser.samples, 96 * len(presets))
            self.assertEqual(parser.inputs, [])
            for figure, preset in zip(parser.examples, presets):
                self.assertEqual(figure['data-static-model'], preset['model'])
                raw = dict(item.split(':', 1) for item in figure['style'].split(';'))
                self.assertEqual(float(raw['--k-raw']), preset['k'])
                self.assertEqual(float(raw['--phase-raw']), preset['phase'])
                self.assertEqual(float(raw['--amplitude-raw']), preset['amplitude'] / 100)
                self.assertIn(preset['file'], parser.links)
            self.assertTrue(audit_html(text, samples=parser.samples)['ok'])
            self.assertEqual(dict(asset_specs(root / 'src'))['gallery.html'], parser.samples)
            styles = (output / 'style.css').read_text()
            engine = (output / 'engine.css').read_text()
            self.assertIn('.gallery-example.lab', styles)
            self.assertIn('animation: none; --clock: 0;', styles)
            self.assertIn('[data-static-model="rose"]', engine)
            self.assertIn('[data-static-model="spiral"]', engine)
            self.assertIn('[data-static-model="orbit"]', engine)

    def test_known_selection_prefix_is_extended_without_copying_math(self):
        source = '.lab:has(#model-test:checked) .sample { --x: calc(sqrt(var(--u))); }'
        result = static_model_selectors(source, [{'id': 'test'}])
        self.assertEqual(result, '.lab:is(:has(#model-test:checked), [data-static-model="test"]) .sample { --x: calc(sqrt(var(--u))); }')
        self.assertEqual(static_model_selectors(result, [{'id': 'test'}]), result)
