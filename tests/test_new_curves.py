import math
import unittest
from tools.coordinates import inspect_snapshot

class NewCurveTests(unittest.TestCase):
    def assert_points(self, model, values, **parameters):
        snap=dict(model=model,k=1,phase_degrees=0,amplitude=.5,clock_radians=0,count=5,stage=dict(x=10,y=20,width=200,height=100),points=[dict(index=i,x=110+44*x,y=70-44*y) for i,x,y in values])
        snap.update(parameters)
        result=inspect_snapshot(snap,1e-9,require_all=True)
        self.assertTrue(result['ok'],result)

    def test_lemniscate_crossings_and_extrema(self):
        p=[(0,.5,0),(1,0,0),(2,-.5,0),(3,0,0),(4,.5,0)]
        self.assert_points('lemniscate',p)

    def test_trochoid_quarter_points_and_cusp(self):
        b=1/math.pi;d=1+b
        self.assert_points('trochoid',[(0,-1/d,1),(1,(-.5-b)/d,0),(2,0,-1),(3,(.5+b)/d,0),(4,1/d,1)],amplitude=1)
        from tools.tangents import tangent_angle
        self.assertIsNone(tangent_angle('trochoid',0,3,0,1,0))
        self.assertIsNone(tangent_angle('trochoid',1,3,0,1,0))

    def test_hypotrochoid_normalized_three_ratio_extrema(self):
        self.assert_points('hypotrochoid',[(0,.5,0),(1,0,.5),(2,-.5,0),(3,0,-.5),(4,.5,0)],k=3)
