import copy
from html.parser import HTMLParser
from pathlib import Path
import unittest
from tools.models import load_models, validate_models, model_tokens, model_styles

ROOT = Path(__file__).resolve().parents[1]


class ModelTests(unittest.TestCase):
    def test_duplicate_invalid_and_incomplete_definitions_are_rejected(self):
        models = load_models(ROOT / 'src')
        invalid = [[], {}, [None], models + [models[0]]]
        for key, value in [('id', 'bad\"id'), ('name', ''), ('equations', ['x'])]:
            changed = copy.deepcopy(models)
            changed[0][key] = value
            invalid.append(changed)
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_models(value)

    def test_selected_model_and_escaped_copy_are_generated_consistently(self):
        models = load_models(ROOT / 'src')
        models[0]['name'] = '<test & name>'
        tokens = model_tokens(models, selected='wave')
        self.assertIn('&lt;test &amp; name&gt;', tokens['@@MODEL_NAMES@@'])
        self.assertNotIn('<test & name>', tokens['@@MODEL_NAMES@@'])
        class Parser(HTMLParser):
            def __init__(self):
                super().__init__(); self.checked = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'input' and 'checked' in attrs:
                    self.checked.append(attrs['value'])
        parser = Parser(); parser.feed(tokens['@@MODEL_CHOICES@@'])
        self.assertEqual(parser.checked, ['wave'])
        self.assertIn('#model-wave:checked', model_styles(models))
        with self.assertRaises(ValueError):
            model_tokens(models, selected='missing')

    def test_each_definition_drives_all_required_display_locations(self):
        models = load_models(ROOT / 'src')
        tokens = model_tokens(models)
        for model in models:
            for token in ('NAMES', 'K_LABELS', 'K_HELP', 'PHASE_HELP', 'AMPLITUDE_LABELS', 'AMPLITUDE_HELP', 'EQUATIONS', 'NOTES'):
                with self.subTest(model=model['id'], token=token):
                    self.assertIn(f'data-model-copy="{model["id"]}"', tokens[f'@@MODEL_{token}@@'])

    def test_initial_fallback_tracks_the_selected_model_in_every_copy(self):
        class Parser(HTMLParser):
            def __init__(self):
                super().__init__(); self.copies = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'data-model-copy' in attrs:
                    self.copies.append((attrs['data-model-copy'], 'data-model-initial' in attrs))
        models = load_models(ROOT / 'src')
        for selected in ('lissajous', 'wave'):
            tokens = model_tokens(models, selected=selected)
            for token, source in tokens.items():
                if token in {'@@MODEL_CHOICES@@', '@@MODEL_REFERENCE@@'}:
                    continue
                with self.subTest(selected=selected, token=token):
                    parser = Parser(); parser.feed(source)
                    self.assertEqual([identifier for identifier, initial in parser.copies if initial], [selected])
                    self.assertEqual(len(parser.copies), len(models))

    def test_css_keeps_initial_copy_visible_before_has_support_branch(self):
        styles = model_styles(load_models(ROOT / 'src'))
        fallback, interactive = styles.split('@supports selector(:has(*))', 1)
        self.assertIn('[data-model-copy][data-model-initial]', fallback)
        self.assertNotIn(':has(', fallback)
        hide = interactive.index('.lab [data-model-copy] { display: none; }')
        self.assertLess(hide, interactive.index('.lab:has(#model-lissajous:checked)'))
        self.assertLess(hide, interactive.index('.lab:has(#model-wave:checked)'))
