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
