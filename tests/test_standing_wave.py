import math
import unittest
from tools.coordinates import inspect_snapshot

class StandingWaveTests(unittest.TestCase):
    def test_nodes_stay_fixed_and_all_points_flatten_at_quarter_cycle(self):
        for clock,heights in ((0,[0,-22,0,22,0]),(math.pi/2,[0,0,0,0,0]),(math.pi,[0,22,0,-22,0])):
            snapshot={'model':'standing-wave','k':1,'phase_degrees':0,'amplitude':.5,
                      'clock_radians':clock,'stage':{'x':10,'y':20,'width':200,'height':100},'count':5,
                      'points':[{'index':i,'x':66+22*i,'y':70+y} for i,y in enumerate(heights)]}
            result=inspect_snapshot(snapshot,tolerance=1e-10)
            self.assertTrue(result['ok'],result['errors'])
            self.assertEqual(result['checked_points'],5)
            snapshot['points'][1]['y']+=.2
            self.assertFalse(inspect_snapshot(snapshot)['ok'])

    def test_phase_moves_nodes_and_fractional_k_does_not_force_fixed_end(self):
        snapshot={'model':'standing-wave','k':1.25,'phase_degrees':0,'amplitude':.5,
                  'clock_radians':0,'stage':{'x':10,'y':20,'width':200,'height':100},'count':5,
                  'points':[{'index':0,'x':66,'y':70},{'index':4,'x':154,'y':48}]}
        self.assertTrue(inspect_snapshot(snapshot,tolerance=1e-10)['ok'])
        snapshot['phase_degrees']=90
        snapshot['points']=[{'index':0,'x':66,'y':48},{'index':4,'x':154,'y':70}]
        self.assertTrue(inspect_snapshot(snapshot,tolerance=1e-10)['ok'])
