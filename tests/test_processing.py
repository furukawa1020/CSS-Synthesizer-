import json
import math
from pathlib import Path
import tempfile
import unittest
from tools.processing import DEFAULTS, processing_options, process_point
from tools.coordinates import inspect_snapshot
from tools.shared_conditions import inspect_shared_batch
from tools.tangents import inspect_tangent_snapshot

class ProcessingTests(unittest.TestCase):
    def test_order_uses_independent_hand_landmark_before_view_transform(self):
        # Original (-1,.5) -> swap (.5,-1) -> fold (.5,1)
        # -> gain (1,1) -> move (.75,1) -> quantum (1,1) -> unit circle.
        p=dict(swap=True,fold='y',gain_x=2,offset_x=-.25,quantum=.5,bound=True)
        s=dict(model='wave',k=1,phase_degrees=90,amplitude=.5,clock_radians=0,
               count=3,stage=dict(x=10,y=20,width=200,height=100),processing=p,
               mirror_x=True,rotation_degrees=90,plot_scale=.75,
               points=[dict(index=0,x=110-33/math.sqrt(2),y=70+33/math.sqrt(2))])
        self.assertTrue(inspect_snapshot(s,1e-10)['ok'])
        s['processing']['swap']=False
        self.assertFalse(inspect_snapshot(s)['ok'])

    def test_round_half_ties_go_toward_positive_and_zero_bound_is_finite(self):
        p=dict(DEFAULTS,quantum=.5)
        self.assertEqual(process_point(-.25,.25,p),(0,.5))
        self.assertAlmostEqual(process_point(-(.1+.05),0,dict(DEFAULTS,quantum=.1))[0],-.1)
        self.assertEqual(process_point(0,0,dict(DEFAULTS,bound=True)),(0,0))
        self.assertEqual(process_point(3,4,dict(DEFAULTS,bound=True)),(.6,.8))
        self.assertEqual(process_point(-.8,.4,dict(DEFAULTS,projection='x',offset_y=.25)),(-.8,.25))
        self.assertEqual(process_point(-.8,.4,dict(DEFAULTS,projection='y',offset_x=.25)),(.25,.4))

    def test_options_reject_nonrepresented_values_and_unknown_keys(self):
        for bad in (None,[],True,{'swap':1},{'bound':'true'},{'fold':[]},{'projection':'both'},
                    {'gain_x':True},{'gain_y':0},{'offset_y':.3},{'quantum':float('nan')},
                    {'quantum':float('inf')},{'surprise':1}):
            with self.subTest(bad=bad):self.assertTrue(processing_options(bad)[1])
        self.assertEqual(processing_options({}),(DEFAULTS,[]))

    def test_processing_metadata_cannot_silently_pass_tangent_inspection(self):
        s=dict(model='wave',k=1,phase_degrees=0,amplitude=.5,clock_radians=0,count=2,
               tangents=[dict(index=0,visible=True,angle_degrees=-math.degrees(math.atan(math.pi/2)))])
        self.assertTrue(inspect_tangent_snapshot(s)['ok'])
        s['processing']={'swap':True}
        self.assertFalse(inspect_tangent_snapshot(s)['ok'])
        s['processing']=None
        self.assertFalse(inspect_tangent_snapshot(s)['ok'])

    def test_shared_processing_must_match_even_when_coordinates_coincide(self):
        common=dict(k=1,phase_degrees=0,amplitude=1,clock_radians=0,count=2,
                    stage=dict(x=0,y=0,width=100,height=100),
                    points=[dict(index=0,x=6,y=50),dict(index=1,x=94,y=50)])
        a=dict(common,model='wave');b=dict(common,model='standing-wave')
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder);m=d/'index.json';m.write_text(json.dumps({'snapshots':['a.json','b.json']}))
            (d/'a.json').write_text(json.dumps(a));(d/'b.json').write_text(json.dumps(b))
            self.assertTrue(inspect_shared_batch(m)['ok'])
            b['processing']={'gain_y':2}
            self.assertTrue(inspect_snapshot(b,require_all=True)['ok'])
            (d/'b.json').write_text(json.dumps(b))
            self.assertFalse(inspect_shared_batch(m)['ok'])
