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

    def test_render_selects_model_count_and_fractional_targets(self):
        from tools.scene import render_scene
        from tools.audit import audit_html
        from html.parser import HTMLParser
        class Inputs(HTMLParser):
            def __init__(self): super().__init__(); self.selected=[]; self.initial=[]
            def handle_starttag(self, tag, pairs):
                a=dict(pairs)
                if tag=='input' and 'checked' in a: self.selected.append(a.get('id'))
                if tag=='span' and 'initial' in a.get('class','').split():self.initial.append(a)
        for count in (96,192,384):
            html=render_scene(self.data(k=3.25,phase=37,amplitude=81,count=count))
            parsed=Inputs();parsed.feed(html)
            self.assertIn('model-rose',parsed.selected)
            self.assertEqual(len(parsed.initial),3)
            self.assertEqual(sum('class="sample"' in s for s in html.split('<i ')),count)
            self.assertTrue(audit_html(html,count)['ok'])
            self.assertIn('--tick-index:2.25',html)
            self.assertIn('反復3.25、位相37°、振幅81%',html)

    def test_clock_is_finite_independent_and_stopped(self):
        from tools.scene import render_scene
        for bad in (True,-.01,7,float('nan')):
            with self.assertRaises(ValueError): validate_scene(self.data(clock_radians=bad))
        html=render_scene(self.data(clock_radians=math.pi))
        self.assertIn('--clock-start:3.1415926535897931;',html)
        self.assertIn('value="stop" checked',html)
        self.assertIn('--phase-raw:90;',html)

    def test_view_only_accepts_real_settings_and_selects_one_radio(self):
        from tools.scene import render_scene
        for bad in ({'point-shape':['shape-round','shape-ring']}, {'point-shape':'time-play'}, {'mirror-x':1}, {'coordinate-fold':'fold-x'}, {'unknown':True}):
            with self.assertRaises(ValueError): validate_scene(self.data(view=bad))
        html=render_scene(self.data(view={'point-shape':'shape-ring','mirror-x':True,'view-labels':False}))
        self.assertRegex(html,r'id="shape-ring"[^>]* checked>')
        self.assertNotRegex(html,r'id="shape-round"[^>]* checked>')
        self.assertNotRegex(html,r'id="view-labels"[^>]* checked>')
