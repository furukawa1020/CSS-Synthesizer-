import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from tools.coordinates import inspect_snapshot
from tools.models import mathml_expression, load_models, model_styles, model_tokens

ROOT = Path(__file__).resolve().parents[1]

class FermatTests(unittest.TestCase):
    def test_square_root_radius_landmarks_and_rotation(self):
        for phase, clock in ((0, 0), (90, 0), (0, math.pi / 2)):
            offsets = [(0, 0), (0, -11), (-22 / math.sqrt(2), 0), (0, 11 * math.sqrt(3)), (22, 0)]
            points = []
            for index, (x, y) in enumerate(offsets):
                if phase or clock:
                    x, y = y, -x
                points.append({'index':index, 'x':110+x, 'y':70+y})
            snapshot = {'model':'fermat', 'k':1, 'phase_degrees':phase, 'amplitude':.5,
                        'clock_radians':clock, 'stage':{'x':10,'y':20,'width':200,'height':100},
                        'count':5, 'points':points}
            with self.subTest(phase=phase, clock=clock):
                result = inspect_snapshot(snapshot, tolerance=1e-10)
                self.assertTrue(result['ok'], result['errors'])
                self.assertEqual(result['checked_points'],5)
                snapshot['points'][2]['x'] += .2
                self.assertFalse(inspect_snapshot(snapshot)['ok'])

    def test_sqrt_is_semantic_math_and_unsupported_selection_has_a_reason(self):
        root = ET.fromstring(mathml_expression('r = A sqrt(u)'))
        ns = {'m':'http://www.w3.org/1998/Math/MathML'}
        self.assertEqual([n.text for n in root.findall('.//m:msqrt/m:mrow/m:mi',ns)],['u'])
        models=load_models(ROOT/'src')
        self.assertIn('@supports not (width: calc(sqrt(.25) * 1px))',model_styles(models))
        self.assertIn('平方根sqrt()',model_tokens(models)['@@MODEL_CHOICES@@'])
