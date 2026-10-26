"""既知の極値と原点を使う独立した座標照合テスト。"""

import copy
import math
import unittest

from tools.coordinates import inspect_snapshot


class CoordinateTests(unittest.TestCase):
    def test_lissajous_known_extrema_keep_the_same_scale_in_both_aspects(self):
        # k=2, phase=0, t=0: theta=pi/4 gives (A,A),
        # theta=3pi/4 gives (-A,-A). Short side 100 => scale 44.
        for width, height, points in (
            (200, 100, [{"index": 1, "x": 132, "y": 48}, {"index": 3, "x": 88, "y": 92}]),
            (100, 200, [{"index": 1, "x": 82, "y": 98}, {"index": 3, "x": 38, "y": 142}]),
        ):
            with self.subTest(width=width, height=height):
                snapshot = {
                    "model": "lissajous", "k": 2, "phase_degrees": 0,
                    "amplitude": .5, "clock_radians": 0,
                    "stage": {"x": 10, "y": 20, "width": width, "height": height},
                    "count": 9, "points": points,
                }
                result = inspect_snapshot(snapshot)
                self.assertTrue(result["ok"], result["errors"])
                self.assertEqual(result["checked_points"], 2)
                self.assertLess(result["max_error"], 1e-12)

    @staticmethod
    def wave_snapshot():
        # phase 90deg + clock pi/2 = pi. Wave endpoints remain +/-44,
        # even though amplitude .5 limits the vertical extrema to +/-22.
        return {
            "model": "wave", "k": 1, "phase_degrees": 90,
            "amplitude": .5, "clock_radians": math.pi / 2,
            "stage": {"x": 10, "y": 20, "width": 200, "height": 100},
            "count": 5,
            "points": [
                {"index": 0, "x": 66, "y": 70},
                {"index": 1, "x": 88, "y": 92},
                {"index": 2, "x": 110, "y": 70},
                {"index": 3, "x": 132, "y": 48},
                {"index": 4, "x": 154, "y": 70},
            ],
        }

    def test_wave_known_points_include_phase_clock_and_amplitude_independent_width(self):
        snapshot = self.wave_snapshot()
        result = inspect_snapshot(snapshot)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["checked_points"], 5)
        self.assertLess(result["max_error"], 1e-12)
        snapshot["points"][2]["x"] += .25
        shifted = inspect_snapshot(snapshot)
        self.assertFalse(shifted["ok"])
        self.assertAlmostEqual(shifted["max_error"], .25)
        self.assertIn("許容差", "\n".join(shifted["errors"]))

    def test_invalid_or_nonfinite_observations_cannot_pass(self):
        base = self.wave_snapshot()
        invalid = [None, {}, {**base, "k": float("nan")}, {**base, "amplitude": float("inf")},
                   {**base, "model": "unknown"}, {**base, "count": True},
                   {**base, "points": []}, {**base, "points": [{"index": 5, "x": 0, "y": 0}]},
                   {**base, "points": [{"index": 0, "x": float("nan"), "y": 0}]},
                   {**base, "points": [base["points"][0], base["points"][0]]}]
        zero_width = copy.deepcopy(base)
        zero_width["stage"]["width"] = 0
        invalid.append(zero_width)
        for snapshot in invalid:
            with self.subTest(snapshot=snapshot):
                result = inspect_snapshot(snapshot)
                self.assertFalse(result["ok"])
                self.assertTrue(result["errors"])
        self.assertFalse(inspect_snapshot(base, tolerance=-1)["ok"])
        self.assertFalse(inspect_snapshot(base, tolerance=float("nan"))["ok"])


if __name__ == "__main__":
    unittest.main()
