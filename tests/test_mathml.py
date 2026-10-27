from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.models import load_models, model_tokens, mathml_expression

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://www.w3.org/1998/Math/MathML'}


class MathMLTests(unittest.TestCase):
    def test_all_model_equations_and_auxiliary_definitions_become_separate_math_rows(self):
        models = load_models(ROOT / 'src')
        root = ET.fromstring('<root>' + model_tokens(models)['@@MODEL_EQUATIONS@@'] + '</root>')
        expected = sum(len(value.split(';')) for model in models for value in model['equations'])
        maths = root.findall('.//m:math', NS)
        self.assertEqual(len(maths), expected)
        self.assertTrue(all(math.get('display') == 'block' for math in maths))
        self.assertTrue(all('data-model-copy' in wrapper.attrib for wrapper in root))
        # Visibility is applied to wrappers, not by overriding MathML layout.
        self.assertTrue(all(math.get('style') is None for math in maths))

    def test_variables_numbers_operators_and_function_application_are_distinct(self):
        math = ET.fromstring(mathml_expression('x = 0.65 cos(kθ + φ − t)'))
        self.assertEqual([node.text for node in math.findall('.//m:mn', NS)], ['0.65'])
        identifiers = math.findall('.//m:mi', NS)
        self.assertEqual([node.text for node in identifiers], ['x','cos','k','θ','φ','t'])
        self.assertEqual(next(node for node in identifiers if node.text == 'cos').get('mathvariant'), 'normal')
        self.assertIn('⁡', [node.text for node in math.findall('.//m:mo', NS)])
        self.assertFalse(math.findall('.//m:mtext', NS))

    def test_unsupported_syntax_and_unbalanced_parentheses_fail_the_build_input(self):
        for expression in ('', 'x=<script>', 'x=A[1]', 'x=sin(θ', 'x=θ)'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                mathml_expression(expression)
