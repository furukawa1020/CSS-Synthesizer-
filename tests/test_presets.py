"""Check starting-state consistency and reject unrepresentable scroll targets."""
import copy
import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.audit import audit_html
from tools.build import ROOT, build
from tools.assets import asset_specs
from tools.presets import load_presets, validate_presets, preset_links


class InitialStateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.checked = {}
        self.initials = []
        self.initial = None
        self.values = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and 'checked' in attrs and attrs.get('name') in {'model', 'time'}:
            self.checked[attrs['name']] = attrs['value']
        if tag == 'main' and attrs.get('class') == 'lab':
            self.values = dict(item.split(':', 1) for item in attrs['style'].split(';'))
        if tag == 'span' and {'tick', 'initial'} <= set(attrs.get('class', '').split()):
            self.initial = ''

    def handle_data(self, data):
        if self.initial is not None:
            self.initial += data

    def handle_endtag(self, tag):
        if tag == 'span' and self.initial is not None:
            self.initials.append(self.initial)
            self.initial = None


class PresetTests(unittest.TestCase):
    def test_each_page_uses_one_consistent_model_time_and_scroll_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            self.assertEqual({p.name for p in output.iterdir()}, {name for name, _ in asset_specs()})
            presets = load_presets(root / 'src')
            for preset in presets:
                with self.subTest(filename=preset['file']):
                    html = (output / preset['file']).read_text()
                    parser = InitialStateParser()
                    parser.feed(html)
                    self.assertEqual(parser.checked, {'model': preset['model'], 'time': 'stop'})
                    self.assertEqual(parser.initials, [f"{preset['k']:.2f}", f"{preset['phase']}°", f"{preset['amplitude']}%"])
                    self.assertEqual(float(parser.values['--k-raw']), preset['k'])
                    self.assertEqual(float(parser.values['--phase-raw']), preset['phase'])
                    self.assertEqual(float(parser.values['--amplitude-raw']), preset['amplitude'] / 100)
                    self.assertTrue(audit_html(html, 192)['ok'])
            standard = InitialStateParser()
            standard.feed((output / 'index.html').read_text())
            self.assertEqual(standard.checked, {'model': 'lissajous', 'time': 'auto'})
            self.assertEqual(standard.initials, ['3.00', '90°', '80%'])

    def test_bad_definitions_cannot_make_inconsistent_initial_targets(self):
        presets = load_presets(ROOT / 'src')
        for key, value in [('file', '../index.html'), ('model', 'missing'), ('k', True),
                           ('k', 3.1), ('phase', 45), ('amplitude', 27), ('name', '')]:
            bad = copy.deepcopy(presets)
            bad[0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_presets(bad)
        bad = copy.deepcopy(presets)
        bad[0]['file'] = bad[1]['file']
        with self.assertRaises(ValueError):
            validate_presets(bad)
        self.assertEqual(tuple(p['file'] for p in presets), tuple(name for name, _ in asset_specs() if name.startswith('preset-')))

    def test_variable_counts_safe_names_and_uniqueness(self):
        presets = load_presets(ROOT / 'src')
        self.assertEqual(validate_presets(presets[:1]), presets[:1])
        for value in ([], presets * 7):
            with self.assertRaises(ValueError):
                validate_presets(value)
        for filename in ('index.html', 'preset-.html', 'preset-../x.html',
                         'preset-X.html', 'preset-x.HTML', 'preset-x/y.html'):
            changed = copy.deepcopy(presets[:1])
            changed[0]['file'] = filename
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                validate_presets(changed)
        changed = copy.deepcopy(presets[:2])
        changed[1]['name'] = ' ' + changed[0]['name'] + ' '
        with self.assertRaises(ValueError):
            validate_presets(changed)

    def test_build_uses_each_fixture_registry_at_call_time(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'src', root / 'src')
            path = root / 'src/presets.json'
            presets = load_presets(root / 'src')
            for count in (1, 2):
                path.write_text(json.dumps(presets[:count]), encoding='utf-8')
                output = build(root)
                expected = {name for name, _ in asset_specs(root / 'src')}
                self.assertEqual({item.name for item in output.iterdir()}, expected)
                self.assertEqual(len(expected), 7 + count)

    def test_names_are_text_and_selected_link_has_page_semantics(self):
        presets = copy.deepcopy(load_presets(ROOT / 'src'))
        presets[0]['name'] = '<script>name</script>'
        links = preset_links(presets, presets[0])
        self.assertNotIn('<script>', links)
        self.assertIn('&lt;script&gt;', links)
        self.assertEqual(links.count('aria-current="page"'), 1)
        self.assertIn('href="index.html"', links)
