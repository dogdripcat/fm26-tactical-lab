"""Static Support UI tests: presentation only, evaluator output remains authoritative."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import connectivity_qualitative_evaluator
import progression_evaluator
import support_evaluator
from test_support_evaluator import fixture
from test_connectivity_engine_v2 import PRESETS, position_only

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "web" / "static" / "js" / "support_presentation_runner.mjs"


def present(v2):
    progression = progression_evaluator.evaluate_progression(
        v2, connectivity_qualitative_evaluator.evaluate_connectivity_v2(v2)
    )
    support = support_evaluator.evaluate_support(v2, progression)
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump({"support_evaluation": support}, handle)
        path = handle.name
    try:
        return json.loads(subprocess.check_output(["node", str(RUNNER), path], text=True, encoding="utf-8")), support
    finally:
        Path(path).unlink()


class SupportUserAnalysisUiTests(unittest.TestCase):
    def test_synthetic_a_to_n_presentation_uses_only_support_evaluator(self):
        cases = {
            "A": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ML", 4, "midfield", "left"), ("DM", 3, "defensive_midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward"), ("CM", "ML", "support"), ("CM", "DM", "backward")]),
            "B": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("DM", 3, "defensive_midfield", "centre")], [("CB", "CM", "forward"), ("CM", "DM", "backward")]),
            "C": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ML", 4, "midfield", "left")], [("CB", "CM", "forward"), ("CM", "ML", "support")]),
            "D": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]),
            "E": fixture([("GK", 0, "goalkeeper", "centre"), ("ST", 6, "forward", "centre")], [("GK", "ST", "forward")], [{"route_id": "GK->ST", "node_ids": ["GK", "ST"]}]),
            "F": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre")], [("CB", "CM", "forward")]),
        }
        for name, v2 in cases.items():
            with self.subTest(case=name):
                view, engine = present(v2)
                self.assertTrue(view["summary"])
                self.assertEqual(3, len(view["cards"]))
                self.assertNotIn("score", json.dumps(view))
                self.assertNotIn("support_evaluation", json.dumps(view))
                self.assertTrue(all("inside" not in card["primary"] and "outside" not in card["primary"] for card in view["cards"]))
                self.assertTrue(all(item["link_ids"] for item in view["advance"]) or not view["advance"])
                self.assertEqual(len(engine["support_isolations"]), len(view["isolated"]))
        terminal_view, _ = present(cases["E"])
        self.assertTrue(any("종착" in row["text"] for row in terminal_view["receivers"]))
        isolated_view, _ = present(cases["F"])
        self.assertTrue(isolated_view["isolated"])

    def test_static_ui_keeps_dimensions_exclusive_and_support_links_existing(self):
        source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("presentSupportEvaluation", source)
        self.assertIn("selectedSupportFocus", source)
        self.assertIn("supportEdges()", source)
        self.assertIn("support-related", source)
        self.assertIn("selectedSupportFocus=null", source)
        self.assertIn('id="support-evaluation"', index)
        self.assertIn("지원 구조", index)
        self.assertNotIn("support_evaluation", index)

    def test_presenter_uses_primary_directions_only_and_terminal_is_neutral(self):
        source = (ROOT / "web" / "static" / "js" / "support_evaluation_presenter.js").read_text(encoding="utf-8")
        self.assertIn("['forward','lateral','recycle']", source)
        self.assertNotIn("support_isolated:'", source)
        self.assertIn("종착 위치", source)
        self.assertIn("구조를 해석하는 보조 근거", source)

    def test_seven_presets_keep_compact_neutral_support_presentation(self):
        for formation, positions in PRESETS.items():
            with self.subTest(formation=formation):
                view, engine = present(position_only(positions))
                self.assertTrue(view["summary"])
                self.assertEqual(3, len(view["cards"]))
                self.assertEqual(len(engine["support_isolations"]), len(view["isolated"]))
                self.assertNotIn("좋습니다", json.dumps(view, ensure_ascii=False))
                self.assertNotIn("점수", json.dumps(view, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()


