import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.coordinates import inspect_snapshot
from tools.models import mathml_expression, load_models, model_styles, model_tokens

ROOT=Path(__file__).resolve().parents[1]
class DampedWaveTests(unittest.TestCase):
    def test_fixed_decay_envelope_cardinal_and_clock_landmarks(self):
        for phase,clock in ((90,0),(0,math.pi/2)):
            offsets=[(-44,-22),(-22,0),(0,22*math.exp(-1.5)),(22,0),(44,-22*math.exp(-3))]
            snapshot={'model':'damped-wave','k':1,'phase_degrees':phase,'amplitude':.5,
                      'clock_radians':clock,'stage':{'x':10,'y':20,'width':200,'height':100},
                      'count':5,'points':[{'index':i,'x':110+x,'y':70+y} for i,(x,y) in enumerate(offsets)]}
            result=inspect_snapshot(snapshot,tolerance=1e-10)
            self.assertTrue(result['ok'],result['errors'])
            self.assertEqual(result['checked_points'],5)
            snapshot['points'][-1]['y']+=.2
            self.assertFalse(inspect_snapshot(snapshot)['ok'])

    def test_exp_is_one_normal_math_function_and_unavailable_model_explained(self):
        root=ET.fromstring(mathml_expression('y=A exp(−3u)'))
        ns={'m':'http://www.w3.org/1998/Math/MathML'}
        identifiers=root.findall('.//m:mi',ns)
        exp=next(n for n in identifiers if n.text=='exp')
        self.assertEqual(exp.get('mathvariant'),'normal')
        models=load_models(ROOT/'src')
        self.assertIn('@supports not (width: calc(exp(0) * 1px))',model_styles(models))
        self.assertIn('指数関数exp()',model_tokens(models)['@@MODEL_CHOICES@@'])
