"""Static Progression UI presentation tests; tactical truth remains in the evaluator."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import connectivity_qualitative_evaluator
import progression_evaluator
from test_connectivity_engine_v2 import PRESETS, position_only
from test_progression_evaluator import fixture

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "web" / "static" / "js" / "progression_presentation_runner.mjs"


def present(v2):
    progression = progression_evaluator.evaluate_progression(v2, connectivity_qualitative_evaluator.evaluate_connectivity_v2(v2))
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump({"connectivity_v2": v2, "progression_evaluation": progression}, handle)
        path = handle.name
    try:
        return json.loads(subprocess.check_output(["node", str(RUNNER), path], text=True, encoding="utf-8")), progression
    finally:
        Path(path).unlink()


class ProgressionUserAnalysisUiTests(unittest.TestCase):
    def test_synthetic_a_to_l_presentation_uses_only_evaluator_outputs(self):
        cases = {
            "A": fixture([("GK", 0, "goalkeeper", "centre"), ("CB", 1, "defensive_line", "centre")], [("GK", "CB", "support")]),
            "B": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]),
            "C": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "ST", "forward")]),
            "D": fixture([("CB", 1, "defensive_line", "centre"), ("AM", 5, "attacking_midfield", "centre")], [("CB", "AM", "forward")]),
            "E": fixture([("CB", 1, "defensive_line", "left"), ("LW", 4, "midfield", "left"), ("ST", 6, "forward", "left")], [("CB", "LW", "forward"), ("LW", "ST", "forward")]),
            "F": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]),
            "G": fixture([("L", 1, "defensive_line", "left"), ("C", 1, "defensive_line", "centre"), ("ST", 6, "forward", "centre")], [("L", "C", "support"), ("C", "ST", "forward")], [{"route_id": "lateral", "node_ids": ["L", "C", "ST"]}]),
            "H": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre")], [("CB", "CM", "forward")]),
            "I": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")], [{"route_id": "one", "node_ids": ["CB", "CM", "ST"]}, {"route_id": "two", "node_ids": ["CB", "CM", "ST"]}]),
            "J": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]),
            "K": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("CM2", 4, "midfield", "right"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward"), ("CB", "CM2", "forward"), ("CM2", "ST", "forward")]),
            "L": fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]),
        }
        for name, v2 in cases.items():
            with self.subTest(case=name):
                view, engine = present(v2)
                self.assertTrue(view["summary"])
                self.assertEqual(len(engine["line_skips"]), len(view["skips"]))
                self.assertEqual(len(engine["advance_then_stall"]), len(view["stalls"]))
                self.assertEqual(len(engine["progression_dependency"]), len(view["dependencies"]))
                self.assertNotIn("score", json.dumps(view))
        self.assertTrue(present(cases["C"])[0]["skips"])
        self.assertFalse(present(cases["D"])[0]["skips"])
        self.assertTrue(present(cases["G"])[0]["lateral"])
        self.assertTrue(present(cases["H"])[0]["stalls"])
        self.assertFalse(present(cases["K"])[0]["dependencies"])
        self.assertTrue(present(cases["L"])[0]["dependencies"])

    def test_all_seven_presets_have_compact_truthful_cards_without_route_count_copy(self):
        for formation, positions in PRESETS.items():
            with self.subTest(formation=formation):
                view, engine = present(position_only(positions))
                self.assertTrue(view["summary"])
                self.assertEqual(view["highest"], {"goalkeeper": "골키퍼 라인", "defensive_line": "수비 라인", "defensive_midfield": "수비형 미드필드 라인", "midfield": "미드필드 라인", "attacking_midfield": "공격형 미드필드 라인", "wing_back_line": "윙백 라인", "forward": "최전방 라인"}[engine["highest_reachable_line"]["vertical_band"]])
                self.assertEqual([card["primary"] for card in view["cards"]], [
                    "전방까지 전진" if engine["regional_advancement"][region]["status"] == "advancement_to_forward" else "중간 라인까지 전진" if engine["regional_advancement"][region]["status"] == "advancement_to_intermediate" else "지원·측면 연결만 가능" if engine["regional_advancement"][region]["status"] == "support_or_lateral_only" else "직접 전진 없음"
                    for region in ("left", "centre", "right")])
                self.assertFalse(view["stalls"])
                self.assertNotIn("경로 수", view["summary"] + view["gainText"])

    def test_static_interaction_state_clears_progression_selection(self):
        source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("selectedProgressionRouteId=null", source)
        self.assertIn("progressionEdges()", source)
        self.assertIn("progression-related", source)
        self.assertIn("$('#progression-evaluation').hidden=true", source)
        self.assertIn("selectedProgressionRouteId=selectedProgressionRouteId===card.representative_route_id?null:card.representative_route_id", source)

    def test_edge_tooltip_uses_football_labels_not_internal_evidence_identifiers(self):
        source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("friendlyPosition(edge.source)", source)
        self.assertIn("analysisBandLabel[basis.source_band]", source)
        self.assertNotIn("semantic.join", source)
        self.assertNotIn("evidence.join", source)


if __name__ == "__main__":
    unittest.main()
