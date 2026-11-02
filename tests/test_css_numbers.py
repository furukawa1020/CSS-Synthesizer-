import math
from pathlib import Path
import unittest
from css_numbers import calculate, declarations
from tools.build import ROOT
from tools.coordinates import inspect_snapshot
from tools.tangents import inspect_tangent_snapshot


class CssNumberChecks(unittest.TestCase):
    def test_new_engine_arithmetic_matches_independent_coordinates_and_tangents(self):
        for model in ('ellipse','astroid','cosine-polar','epitrochoid'):
            definitions=declarations((ROOT/f'src/engines/{model}.css').read_text())
            for k,phase,amplitude,clock in ((1,0,.25,0),(3.17,93,.8,1.37),(8,360,1,6)):
                for count in (96,192,384):
                    points=[];tangents=[]
                    for i in range(count):
                        values={'k':k,'phase':math.radians(phase),'amplitude':amplitude,'clock':clock,'theta':math.tau*i/(count-1)}
                        x=calculate('x',definitions,values);y=calculate('y',definitions,values)
                        dx=calculate('tangent-dx',definitions,values);dy=calculate('tangent-dy',definitions,values)
                        visible=math.hypot(dx,dy)>=1e-6
                        points.append(dict(index=i,x=100+44*x,y=50-44*y))
                        tangents.append(dict(index=i,visible=visible,angle_degrees=math.degrees(math.atan2(-dy,dx))))
                    snapshot=dict(model=model,k=k,phase_degrees=phase,amplitude=amplitude,clock_radians=clock,count=count,stage=dict(x=0,y=0,width=200,height=100),points=points,tangents=tangents)
                    with self.subTest(model=model,k=k,count=count):
                        a=inspect_snapshot(snapshot,1e-8,require_all=True)
                        b=inspect_tangent_snapshot(snapshot,1e-7,require_all=True)
                        self.assertTrue(a['ok'],a);self.assertTrue(b['ok'],b)

    def test_metric_color_and_opacity_arithmetic_has_defined_boundaries(self):
        colors=declarations((ROOT/'src/styles/zz-metric-color.css').read_text())
        opacity=declarations((ROOT/'src/styles/zz-radius-opacity.css').read_text())
        for x,y,angle in ((1,0,0),(0,1,90),(-1,0,180),(0,-1,270),(0,0,0),(-0.0,-0.0,0)):
            values={'draw-x':x,'draw-y':y}
            self.assertAlmostEqual(math.degrees(calculate('angle-hue',colors,values))%360,angle)
        for radius,hue,factor in ((0,30,.25),(.5,120,.625),(1,210,1),(2,210,1)):
            values={'draw-x':radius,'draw-y':0}
            self.assertAlmostEqual(calculate('metric-hue',colors,values),hue)
            self.assertAlmostEqual(calculate('radius-opacity',opacity,values),factor)

    def test_clock_source_arithmetic_wraps_forward_and_reverse_from_saved_origin(self):
        definitions=declarations((ROOT/'src/engine.css').read_text())
        for origin in (0,1.2,math.tau):
            start=calculate('clock',definitions,{'clock-start':origin,'clock-progress':0})
            reverse_start=calculate('clock',definitions,{'clock-start':origin,'clock-progress':math.tau})
            self.assertAlmostEqual(start,origin%math.tau)
            self.assertAlmostEqual(reverse_start,start)
            for elapsed in (.01,.5,2,6):
                progress=math.tau-elapsed
                actual=calculate('clock',definitions,{'clock-start':origin,'clock-progress':progress})
                self.assertAlmostEqual(actual,(origin-elapsed)%math.tau)
                self.assertGreaterEqual(actual,0);self.assertLess(actual,math.tau)

    def test_enlargement_and_270_degree_rotation_keep_unclipped_coordinates(self):
        for scale in (1.25,1.5):
            snapshot=dict(model='wave',k=1,phase_degrees=0,amplitude=.5,clock_radians=0,count=3,rotation_degrees=270,plot_scale=scale,stage=dict(x=0,y=0,width=100,height=100),points=[dict(index=0,x=50,y=50-44*scale),dict(index=1,x=50,y=50),dict(index=2,x=50,y=50+44*scale)])
            self.assertTrue(inspect_snapshot(snapshot,1e-9,require_all=True)['ok'])
            snapshot['plot_scale']=1.4
            self.assertFalse(inspect_snapshot(snapshot)['ok'])
