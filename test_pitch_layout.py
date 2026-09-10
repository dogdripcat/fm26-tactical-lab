import unittest

from web import api
from web.pitch_layout import CENTER_X


class PitchLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = api.pitch_layout_payload_for_presets()

    def test_4231_central_spine_and_pairs_are_symmetric(self):
        positions = self.layout["coordinates"]["4-2-3-1"]
        self.assertEqual(CENTER_X, positions["ST"][0])
        self.assertEqual(CENTER_X, positions["AMC"][0])
        self.assertEqual(CENTER_X, positions["GK"][0])
        for left, right in (("AML", "AMR"), ("DML", "DMR"), ("LCB", "RCB"), ("LB", "RB")):
            self.assertEqual(CENTER_X - positions[left][0], positions[right][0] - CENTER_X)

    def test_all_presets_are_bounded_and_keep_required_symmetry(self):
        for name, positions in self.layout["coordinates"].items():
            for x, y in positions.values():
                self.assertGreaterEqual(x, 0, name)
                self.assertLessEqual(x, 100, name)
                self.assertGreaterEqual(y, 0, name)
                self.assertLessEqual(y, 100, name)
            for left, right in (("LB", "RB"), ("wing_back_left", "wing_back_right"), ("LCB", "RCB"), ("DML", "DMR"), ("MCL", "MCR"), ("AML", "AMR")):
                if left in positions and right in positions:
                    self.assertEqual(CENTER_X - positions[left][0], positions[right][0] - CENTER_X, name)
            for central in ("GK", "DC", "DM", "MC", "AMC"):
                if central in positions:
                    self.assertEqual(CENTER_X, positions[central][0], name)

    def test_three_back_presets_keep_dedicated_wing_back_coordinates(self):
        for formation in ("3-4-2-1", "3-4-3", "3-5-2"):
            positions = self.layout["coordinates"][formation]
            self.assertIn("wing_back_left", positions)
            self.assertIn("wing_back_right", positions)
            self.assertEqual(CENTER_X - positions["wing_back_left"][0], positions["wing_back_right"][0] - CENTER_X)

    def test_web_assets_define_football_markings(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("renderPitchMarkings", script)
        self.assertIn("cx=\"50\" cy=\"75\" r=\"13\"", script)
        self.assertIn("x1=\"1\" y1=\"75\" x2=\"99\" y2=\"75\"", script)
        self.assertIn("width=\"56\" height=\"18\"", script)
        self.assertIn("width=\"30\" height=\"7\"", script)


if __name__ == "__main__":
    unittest.main()
