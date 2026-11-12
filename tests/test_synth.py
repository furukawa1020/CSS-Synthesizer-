from html.parser import HTMLParser
from pathlib import Path
import unittest

from tools.audit import audit_html
from tools.assets import asset_specs
from tools.synth import DEFAULTS, PATCHES, SAMPLE_COUNT, synth_html


class SynthMarkup(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.selected = {}
        self.current = []
        self.controls = set()
        self.trace_points = 0
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select':
            self.select_name = attrs['name']
        if tag == 'option' and 'selected' in attrs:
            self.selected[self.select_name] = attrs['value']
        if tag == 'a' and attrs.get('aria-current') == 'page':
            self.current.append(attrs['href'])
        if tag in ('input', 'button'):
            self.controls.add((tag, attrs.get('id'), attrs.get('type'), 'checked' in attrs))
        if tag == 'i':
            self.trace_points += 1


class SynthTests(unittest.TestCase):
    def test_each_patch_builds_as_an_independently_resettable_editor(self):
        template = (Path(__file__).resolve().parents[1] / 'src/synth.html').read_text(encoding='utf-8')
        assets = dict(asset_specs())
        self.assertEqual(assets['samples-192.html'], SAMPLE_COUNT)
        for filename, (_, settings, _) in PATCHES.items():
            with self.subTest(filename=filename):
                page = synth_html(template, filename)
                self.assertNotIn('@@', page)
                self.assertEqual(assets[filename], SAMPLE_COUNT)
                self.assertTrue(audit_html(page, SAMPLE_COUNT)['ok'])
                markup = SynthMarkup(page)
                self.assertEqual(markup.selected, DEFAULTS | settings)
                self.assertEqual(markup.current, [filename])
                self.assertEqual(markup.trace_points, 3 * SAMPLE_COUNT)
                self.assertIn(('input', 's-zero', 'radio', True), markup.controls)
                self.assertIn(('input', 's-manual', 'radio', False), markup.controls)
                self.assertIn(('input', 's-grid', 'checkbox', True), markup.controls)
                self.assertIn(('button', None, 'reset', False), markup.controls)


    def test_effect_presets_set_only_the_intended_defaults(self):
        _, pulse, _ = PATCHES['synth-pulse.html']
        _, fold, _ = PATCHES['synth-fold.html']
        self.assertEqual((pulse['mix'], pulse['b-wave'], pulse['b-duty']),
                         ('amplitude', 'square', '90deg'))
        self.assertEqual((fold['view'], fold['mix'], fold['shape'], fold['gain']),
                         ('polar', 'solo-a', 'fold', '2'))
