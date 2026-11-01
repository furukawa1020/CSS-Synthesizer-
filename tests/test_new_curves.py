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
