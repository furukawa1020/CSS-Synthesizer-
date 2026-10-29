"""Check analytic directions using independent centered finite differences."""
import math
import unittest
from tools.tangents import MODELS, inspect_tangent_snapshot, tangent_angle


def position(model, u, k, phi, a, t):
    theta = math.tau * u
    if model == 'lissajous':
        return a * math.sin(k * theta + phi + t), a * math.sin(2 * theta + t)
    if model in {'wave', 'damped-wave', 'standing-wave'}:
        y = a * math.sin(k * theta + phi + t)
        if model == 'damped-wave':
            y *= math.exp(-3 * u)
        if model == 'standing-wave':
            y = a * math.sin(k * theta + phi) * math.cos(t)
        return 2 * u - 1, y
    if model in {'spiral', 'fermat', 'rose'}:
        radius = a * (u if model == 'spiral' else math.sqrt(u))
        angle = k * theta + phi + t
        if model == 'rose':
            radius, angle = a * math.sin(k * theta + phi), theta + t
        return radius * math.cos(angle), radius * math.sin(angle)
    return a * (.65 * math.cos(theta+t) + .35 * math.cos(k*theta+phi-t)), a * (.65 * math.sin(theta+t) - .35 * math.sin(k*theta+phi-t))


class TangentTests(unittest.TestCase):
    def test_all_models_match_position_finite_differences(self):
        for model in MODELS:
            for k, phase, a, clock in ((1, 0, .25, 0), (3.17, 93, .8, 1.37), (8, 360, 1, 6)):
                for u in (.013, .227, .593, .981):
                    with self.subTest(model=model, k=k, u=u):
                        left = position(model, u-1e-7, k, math.radians(phase), a, clock)
                        right = position(model, u+1e-7, k, math.radians(phase), a, clock)
                        angle = math.degrees(math.atan2(-(right[1]-left[1]), right[0]-left[0]))
                        expected = tangent_angle(model, u, k, phase, a, clock)
                        self.assertIsNotNone(expected)
                        self.assertLess(abs((angle-expected+180)%360-180), .0001)

    def test_fermat_origin_uses_one_sided_limit(self):
        for phase, clock in ((0, 0), (90, .2), (360, 5)):
            x, y = position('fermat', 1e-10, 8, math.radians(phase), .8, clock)
            angle = math.degrees(math.atan2(-y, x))
            expected = tangent_angle('fermat', 0, 8, phase, .8, clock)
            self.assertLess(abs((angle-expected+180)%360-180), .0001)

    def test_zero_vector_is_hidden_and_direction_wraps(self):
        # k=2, phi=t=0, theta=pi/4 gives both derivative components zero.
        snap = {'model':'lissajous','k':2,'phase_degrees':0,'amplitude':.5,'clock_radians':0,'count':9,'tangents':[{'index':1,'visible':False}]}
        self.assertTrue(inspect_tangent_snapshot(snap)['ok'])
        snap['tangents'][0]['visible'] = True
        self.assertFalse(inspect_tangent_snapshot(snap)['ok'])
        snap.update(model='wave', count=2, phase_degrees=90)
        snap['tangents'] = [{'index':0,'visible':True,'angle_degrees':360}]
        self.assertTrue(inspect_tangent_snapshot(snap)['ok'])
        snap['tangents'][0]['angle_degrees'] = 90
        self.assertFalse(inspect_tangent_snapshot(snap)['ok'])

    def test_invalid_observation_is_rejected(self):
        snap = {'model':'wave','k':1,'phase_degrees':0,'amplitude':.5,'clock_radians':0,'count':2,'tangents':[{'index':0,'visible':True,'angle_degrees':float('nan')}]}
        self.assertFalse(inspect_tangent_snapshot(snap)['ok'])
        for key, value in (('model',[]), ('k',True), ('count',True), ('tangents',[])):
            changed = dict(snap); changed[key] = value
            self.assertFalse(inspect_tangent_snapshot(changed)['ok'])
