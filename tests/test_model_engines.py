"""A metadata-only model must not quietly render the default curve."""
import copy
import re
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.build import ROOT, build
from tools.coordinates import SUPPORTED_MODELS
from tools.models import load_models
from tools.model_engines import validate_engine_models
from tools.source import compose_css


class ModelEngineTests(unittest.TestCase):
    def test_current_bindings_and_base_lissajous_match_checker(self):
        models = load_models(ROOT / 'src')
        css = compose_css(ROOT / 'src', 'engine.css')
        result = validate_engine_models(models, css)
        self.assertEqual(set(result['models']), SUPPORTED_MODELS)
        self.assertEqual(result['default_models'], ['lissajous'])
        self.assertIn('wave', result['bindings'])
        # Comments and content strings are not authored checked-model bindings.
        ignored = '/* .lab:has(#model-ghost:checked) */ .x { content:".lab:has(#model-ghost:checked)" }'
        self.assertEqual(validate_engine_models(models, css + ignored), result)

    def test_unknown_metadata_missing_selector_and_extra_alias_are_rejected(self):
        models = load_models(ROOT / 'src')
        css = compose_css(ROOT / 'src', 'engine.css')
        unknown = copy.deepcopy(models)
        unknown.append({**unknown[0], 'id': 'unknown'})
        for definitions, source, supported in (
            (unknown, css, SUPPORTED_MODELS),
            (models, css.replace('.lab:has(#model-wave:checked)', '.lab.never'), SUPPORTED_MODELS),
            (models, css + '\n.lab:has(#model-ghost:checked) .sample { color:red }', SUPPORTED_MODELS),
            (models, css, SUPPORTED_MODELS - {'wave'}),
            (models[1:], css, SUPPORTED_MODELS - {'lissajous'}),
        ):
            with self.subTest(ids=[m['id'] for m in definitions]), self.assertRaises(ValueError):
                validate_engine_models(definitions, source, supported)

    def test_tangent_only_selector_is_not_a_coordinate_binding(self):
        models = load_models(ROOT / 'src')
        css = compose_css(ROOT / 'src', 'engine.css')
        source = re.sub(
            r'(\.lab:has\(#model-wave:checked\)\s+\.sample\s*\{)[^{}]*}',
            r'\1 --tangent-dx: 2; --tangent-dy: 3; }', css,
        )
        source += '\n.lab:has(#model-wave:checked) .sample { --tangent-dx: 2; --tangent-dy: 3; }'
        with self.assertRaisesRegex(ValueError, 'CSS描画selector'):
            validate_engine_models(models, source)
        # A declaration for only one coordinate is insufficient as well.
        source += '\n.lab:has(#model-wave:checked) .sample { --x: 1; }'
        with self.assertRaisesRegex(ValueError, 'CSS描画selector'):
            validate_engine_models(models, source)

    def test_binding_failure_keeps_previous_build(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            path = root / 'src/engine.css'
            path.write_text(path.read_text().replace('.lab:has(#model-wave:checked)', '.lab.never'))
            with self.assertRaisesRegex(ValueError, 'CSS描画selector'):
                build(root)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
            self.assertEqual(list(root.glob('.build-candidate-*')), [])
