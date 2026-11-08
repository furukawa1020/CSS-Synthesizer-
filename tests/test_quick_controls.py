"""Regression checks for the native inputs and legacy entry boundaries."""
from html.parser import HTMLParser
import unittest
from tools.build import ROOT, single_html
from tools.models import load_models
from tools.presets import load_presets
from tools.scene import render_scene
from tools.source import expand_fragments


class Inputs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.ids = []
        self.forms = []
        self.buttons = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'input':
            self.inputs.append(a)
        if tag == 'form':
            self.forms.append(a.get('id'))
        if tag == 'button':
            self.buttons.append(a)


class QuickControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / 'src'
        cls.template = expand_fragments((source / 'page.html').read_text(), source)
        cls.models = load_models(source)
        cls.presets = load_presets(source)
    def test_all_registered_values_have_exactly_one_native_start_and_reset(self):
        for preset in self.presets:
            with self.subTest(file=preset['file']):
                html = single_html(self.template, self.models, self.presets, 192, preset)
                parser = Inputs()
                parser.feed(html)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                self.assertEqual(parser.forms.count('quick-values'), 1)
                for key in ('k', 'phase', 'amplitude'):
                    group = [a for a in parser.inputs if a.get('name') == 'quick-' + key]
                    selected = [a for a in group if 'checked' in a]
                    self.assertTrue(all(a.get('form') == 'quick-values' for a in group))
                    self.assertEqual(len(selected), 1)
                    self.assertEqual(float(selected[0]['value']), preset[key])
                    self.assertEqual(len({a['value'] for a in group}), len(group))
                self.assertTrue(any(a.get('type') == 'reset' for a in parser.buttons))
    def test_legacy_exports_keep_exact_inputs_and_three_time_options(self):
        html = render_scene(dict(version=1, model='rose', k=2.37, phase=17, amplitude=73))
        self.assertNotIn('id="quick-values"', html)
        self.assertNotIn('id="time-zero"', html)
        parser = Inputs()
        parser.feed(html)
        self.assertEqual(len([a for a in parser.inputs if a.get('name') == 'time']), 3)
        self.assertIn('--k-raw:2.37;--phase-raw:17;--amplitude-raw:0.73', html)
    def test_home_has_both_input_modes_and_zero_time(self):
        html = single_html(self.template, self.models, self.presets, 192, home=True)
        parser = Inputs()
        parser.feed(html)
        states = {a.get('id'): a for a in parser.inputs}
        self.assertIn('checked', states['input-basic'])
        self.assertNotIn('checked', states['input-scroll'])
        self.assertEqual(states['time-zero']['name'], 'time')
        self.assertEqual(states['time-zero']['value'], 'zero')
