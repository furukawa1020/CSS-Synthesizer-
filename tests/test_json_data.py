from pathlib import Path
import shutil
import tempfile
import unittest

from tools.build import ROOT, build
from tools.json_data import loads_json
from tools.models import load_models
from tools.presets import load_presets


class StrictJSONTests(unittest.TestCase):
    def test_ordinary_values_are_preserved(self):
        self.assertEqual(loads_json('{"name":"花弁", "values":[1, 0.5, true, null]}'),
                         {'name': '花弁', 'values': [1, .5, True, None]})

    def test_duplicates_and_nonfinite_numbers_are_rejected(self):
        for text in ('{"id": "a", "id": "b"}', '{"nested":{"x":1,"x":2}}',
                     '[NaN]', '[Infinity]', '[-Infinity]', '[1e9999]'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                loads_json(text)

    def test_each_registry_uses_the_strict_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for filename, loader in (('models.json', load_models), ('presets.json', load_presets)):
                (source / filename).write_text('[{"id":"first","id":"last"}]')
                with self.subTest(filename=filename), self.assertRaisesRegex(ValueError, '重複'):
                    loader(source)

    def test_invalid_registry_does_not_replace_a_successful_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'src', root / 'src')
            output = build(root)
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            (root / 'src/models.json').write_text('[{"id":"first","id":"last"}]')
            with self.assertRaisesRegex(ValueError, '重複'):
                build(root)
            self.assertEqual(before, {path.name: path.read_bytes() for path in output.iterdir()})
            self.assertEqual(list(root.glob('.build-candidate-*')), [])
