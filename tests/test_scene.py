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

    def test_inputs_use_the_displayed_precision(self):
        for key, bad in [('k',True),('k',0),('k',8.01),('k',1.001),('phase',90.1),('amplitude',24),('amplitude',80.1),('k',float('inf'))]:
            with self.subTest(key=key,bad=bad), self.assertRaises(ValueError): validate_scene(self.data(**{key:bad}))
        self.assertEqual(validate_scene(self.data(k=1.01, phase=359, amplitude=26))['k'],1.01)
