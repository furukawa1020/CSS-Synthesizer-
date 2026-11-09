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
        self.select = None
        self.details = []
        self.band_parents = []
        self.work_default = None
        self.guide_parents = ()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'details':
            self.details.append(a.get('class', ''))
            if a.get('class') == 'work-options':
                self.work_default = 'open' in a
        if 'input-band' in a.get('class', '').split():
            self.band_parents.append(tuple(self.details))
        if a.get('id') == 'guide-start':
            self.guide_parents = tuple(self.details)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'input':
            self.inputs.append(a)
        if tag == 'select':
            self.select = a
        if tag == 'option' and self.select:
            option = dict(a, name=self.select['name'], form=self.select.get('form'))
            if 'selected' in a:
                option['checked'] = ''
            self.inputs.append(option)
        if tag == 'form':
            self.forms.append(a.get('id'))
        if tag == 'button':
            self.buttons.append(a)

    def handle_endtag(self, tag):
        if tag == 'details':
            self.details.pop()
        if tag == 'select':
            self.select = None


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
                self.assertTrue(all(a.get('form') == 'quick-values' for a in parser.inputs if a.get('name', '').startswith('quick-')))
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

    def test_home_has_three_selects_with_one_default_option_each(self):
        html = single_html(self.template, self.models, self.presets, 192, home=True)
        self.assertEqual(html.count('<select '), 3)
        self.assertNotIn('type="radio" form="quick-values"', html)
        for key, value in (('k', 2), ('phase', 90), ('amplitude', 70)):
            parser = Inputs()
            parser.feed(html)
            options = [a for a in parser.inputs if a.get('name') == 'quick-' + key]
            defaults = [a for a in options if 'selected' in a]
            self.assertEqual(len(defaults), 1)
            self.assertEqual(float(defaults[0]['value']), value)

    def test_home_keeps_bands_outside_the_single_settings_entry(self):
        html = single_html(self.template, self.models, self.presets, 192, home=True)
        parser = Inputs()
        parser.feed(html)
        self.assertEqual(parser.band_parents, [(), (), ()])
        self.assertIs(parser.work_default, False)
        self.assertIn('work-options', parser.guide_parents)
        self.assertIn('explanation', parser.guide_parents)
        self.assertIn('guide-section', parser.guide_parents)
        self.assertIn('href="#guide-start"', html)
