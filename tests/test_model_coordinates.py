"""Analytic landmarks for the additional models, independent of CSS values."""
import math
import unittest
from tools.coordinates import inspect_snapshot


class ExtraModelCoordinateTests(unittest.TestCase):
    @staticmethod
    def snapshot(model, points, **parameters):
        return {
            'model': model, 'k': 2, 'phase_degrees': 90, 'amplitude': .5,
            'clock_radians': 0, 'stage': {'x': 10, 'y': 20, 'width': 200, 'height': 100},
            'count': 5, 'points': [{'index': index, 'x': x, 'y': y} for index, x, y in points],
            **parameters,
        }

    def test_rose_signed_radius_cardinal_points_and_clock_rotation(self):
        for clock, points in (
            (0, [(0,132,70),(1,110,92),(2,88,70),(3,110,48),(4,132,70)]),
            (math.pi/2, [(0,110,48),(1,132,70),(2,110,92),(3,88,70),(4,110,48)]),
        ):
            with self.subTest(clock=clock):
                result = inspect_snapshot(self.snapshot('rose', points, clock_radians=clock), tolerance=1e-10)
                self.assertTrue(result['ok'], result['errors'])
                self.assertEqual(result['checked_points'], 5)

    def test_rose_fractional_repetition_can_leave_open_endpoints_and_reject_errors(self):
        snapshot = self.snapshot('rose', [(0,132,70),(4,110,70)], k=1.25)
        self.assertTrue(inspect_snapshot(snapshot, tolerance=1e-10)['ok'])
        snapshot['points'][1]['x'] += .25
        self.assertFalse(inspect_snapshot(snapshot)['ok'])

    def test_spiral_radius_grows_at_known_quarter_turns(self):
        snapshot = self.snapshot('spiral', [(0,110,70),(1,110,64.5),(2,99,70),(3,110,86.5),(4,132,70)], k=1, phase_degrees=0)
        result = inspect_snapshot(snapshot, tolerance=1e-10)
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['checked_points'], 5)
        # Same short side, another aspect ratio: every point keeps its offset.
        snapshot['stage'] = {'x': 10, 'y': 20, 'width': 100, 'height': 200}
        for point in snapshot['points']:
            point['x'] -= 50
            point['y'] += 50
        self.assertTrue(inspect_snapshot(snapshot, tolerance=1e-10)['ok'])

    def test_spiral_phase_clock_and_turn_count_have_separate_meanings(self):
        rotated = [(0,110,70),(1,104.5,70),(2,110,81),(3,126.5,70),(4,110,48)]
        for phase, clock in ((90,0),(0,math.pi/2)):
            with self.subTest(phase=phase, clock=clock):
                result = inspect_snapshot(self.snapshot('spiral', rotated, k=1, phase_degrees=phase, clock_radians=clock), tolerance=1e-10)
                self.assertTrue(result['ok'], result['errors'])
        result = inspect_snapshot(self.snapshot('spiral', [(1,104.5,70),(2,121,70),(3,93.5,70),(4,132,70)], k=2, phase_degrees=0), tolerance=1e-10)
        self.assertTrue(result['ok'], result['errors'])
