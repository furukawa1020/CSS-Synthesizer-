"""Check every model is independently readable in the static guide."""
import copy
from html.parser import HTMLParser
from pathlib import Path
import unittest
from tools.models import load_models, model_reference_html, model_tokens

ROOT = Path(__file__).resolve().parents[1]


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.details = []
        self.math = 0
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append(tag)
        if tag == 'details':
            self.details.append(attributes.get('id'))
        if tag == 'math':
            self.math += 1


class ModelReferenceTests(unittest.TestCase):
    def test_all_models_have_independent_native_details_and_all_equation_rows(self):
        models = load_models(ROOT / 'src')
        source = model_reference_html(models)
        parser = ReferenceParser(); parser.feed(source)
        self.assertEqual(parser.details, ['model-reference-' + m['id'] for m in models])
        self.assertEqual(parser.math, sum(len(eq.split(';')) for m in models for eq in m['equations']))
        self.assertNotIn('data-model-copy', source)
        self.assertNotIn('data-model-initial', source)
        for model in models:
            for key in ('name', 'k_label', 'k_help', 'phase_help', 'amplitude_label', 'amplitude_help', 'note'):
                with self.subTest(model=model['id'], key=key):
                    self.assertIn(model[key], source)
        self.assertIn('固定端の境界条件を保証しません', source)
        self.assertIn('減衰率3は固定', source)
        self.assertEqual(model_tokens(models, selected='wave')['@@MODEL_REFERENCE@@'], source)

    def test_labels_are_text_and_css_capability_does_not_hide_explanation(self):
        models = copy.deepcopy(load_models(ROOT / 'src'))
        models[0]['name'] = '<script>not markup</script>'
        source = model_reference_html(models)
        parser = ReferenceParser(); parser.feed(source)
        self.assertNotIn('script', parser.tags)
        self.assertIn('&lt;script&gt;not markup&lt;/script&gt;', source)
        self.assertEqual(source.count('説明と式は対応の有無にかかわらず読めます'), 2)
