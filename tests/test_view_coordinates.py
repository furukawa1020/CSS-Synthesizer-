"""Known coordinates for view reflection, independent of browser CSS values."""
import copy
import unittest
from tools.coordinates import inspect_snapshot


class ViewCoordinateTests(unittest.TestCase):
    @staticmethod
    def wave():
        # x = -1,0,+1; phase90deg gives y = +.5,-.5,+.5.
        # Origin(110,70), common scale44px.
        return {
            "model": "wave", "k": 1, "phase_degrees": 90,
            "amplitude": .5, "clock_radians": 0,
            "stage": {"x": 10, "y": 20, "width": 200, "height": 100},
            "count": 3,
            "points": [{"index": 0, "x": 66, "y": 48},
                       {"index": 1, "x": 110, "y": 92},
                       {"index": 2, "x": 154, "y": 48}],
        }

    def test_missing_flags_and_explicit_false_keep_existing_coordinates(self):
        snapshot = self.wave()
        self.assertTrue(inspect_snapshot(snapshot)["ok"])
        snapshot.update(mirror_x=False, mirror_y=False)
        self.assertTrue(inspect_snapshot(snapshot)["ok"])

    def test_wave_known_points_reflect_in_each_direction(self):
        for mirror_x, mirror_y, coordinates in (
            (True, False, [(154, 48), (110, 92), (66, 48)]),
            (False, True, [(66, 92), (110, 48), (154, 92)]),
            (True, True, [(154, 92), (110, 48), (66, 92)]),
        ):
            with self.subTest(x=mirror_x, y=mirror_y):
                snapshot = self.wave()
                snapshot.update(mirror_x=mirror_x, mirror_y=mirror_y)
                snapshot["points"] = [
                    {"index": index, "x": x, "y": y}
                    for index, (x, y) in enumerate(coordinates)
                ]
                result = inspect_snapshot(snapshot, tolerance=1e-10)
                self.assertTrue(result["ok"], result["errors"])
                self.assertEqual(result["checked_points"], 3)

    def test_lissajous_reflection_keeps_short_side_scale(self):
        # theta=pi/4, k=2, phase=t=0 => x=y=.5. Both signs flip.
        snapshot = {
            "model": "lissajous", "k": 2, "phase_degrees": 0,
            "amplitude": .5, "clock_radians": 0,
            "stage": {"x": 10, "y": 20, "width": 100, "height": 200},
            "count": 9, "mirror_x": True, "mirror_y": True,
            "points": [{"index": 1, "x": 38, "y": 142}],
        }
        result = inspect_snapshot(snapshot, tolerance=1e-10)
        self.assertTrue(result["ok"], result["errors"])

    def test_unreflected_points_do_not_pass_when_reflection_is_requested(self):
        for flag in ("mirror_x", "mirror_y"):
            with self.subTest(flag=flag):
                snapshot = self.wave()
                snapshot[flag] = True
                result = inspect_snapshot(snapshot)
                self.assertFalse(result["ok"])
                self.assertGreater(result["max_error"], 40)

    def test_reflection_flags_accept_only_booleans(self):
        for flag in ("mirror_x", "mirror_y"):
            for invalid in (None, 0, 1, "false", "true", [], {}):
                with self.subTest(flag=flag, value=invalid):
                    snapshot = copy.deepcopy(self.wave())
                    snapshot[flag] = invalid
                    result = inspect_snapshot(snapshot, tolerance=1000)
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["checked_points"], 0)
                    self.assertIn(flag, "\n".join(result["errors"]))
