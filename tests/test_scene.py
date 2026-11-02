import json
import math
from pathlib import Path
import tempfile
import unittest
from tools.scene import validate_scene, load_scene

class SceneTests(unittest.TestCase):
    def data(self, **kw): return dict(version=1, model='rose', **kw)

    def test_schema_and_bounded_strict_json(self):
        self.assertEqual(validate_scene(self.data())['count'], 192)
        for bad in ([], {}, self.data(surprise=True), self.data(count=True), dict(version=True,model='rose'), dict(version=1,model='unknown')):
            with self.subTest(bad=bad), self.assertRaises(ValueError): validate_scene(bad)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'scene.json'
            for raw in ('{"version":1,"version":1,"model":"rose"}', '{"version":1,"model":"rose","k":NaN}', ' '*16385):
                path.write_text(raw)
                with self.assertRaises(ValueError): load_scene(path)
