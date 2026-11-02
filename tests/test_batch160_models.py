import math
import unittest
from tools.coordinates import inspect_snapshot
from tools.tangents import tangent_angle

class DrawingModelsTests(unittest.TestCase):
    def landmarks(self,model,points,k=1):
        s=dict(model=model,k=k,phase_degrees=0,amplitude=.5,clock_radians=0,count=5,stage=dict(x=10,y=20,width=200,height=100),points=[dict(index=i,x=110+44*x,y=70-44*y) for i,(x,y) in enumerate(points)])
        result=inspect_snapshot(s,1e-9,require_all=True)
        self.assertTrue(result['ok'],result)

    def test_ellipse_axis_ratio_landmarks(self):
        self.landmarks('ellipse',[(.5,0),(0,.25),(-.5,0),(0,-.25),(.5,0)],k=2)

    def test_astroid_cusps_have_positions_but_no_tangents(self):
        self.landmarks('astroid',[(.5,0),(0,.5),(-.5,0),(0,-.5),(.5,0)])
        for u in (0,.25,.5,.75,1):self.assertIsNone(tangent_angle('astroid',u,1,0,.5,0))

    def test_cardioid_landmarks_and_origin_cusp(self):
        self.landmarks('cosine-polar',[(.5,0),(0,.25),(0,0),(0,-.25),(.5,0)])
        self.assertIsNone(tangent_angle('cosine-polar',.5,1,0,.5,0))
