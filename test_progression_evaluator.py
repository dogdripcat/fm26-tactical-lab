import copy
import json
import os
import subprocess
import tempfile
import unittest

import connectivity_qualitative_evaluator
import fm26lab
import progression_evaluator
import role_behaviours
import role_constraints
from core.pipeline import analyze_tactic_data
from test_connectivity_engine_v2 import PRESETS, position_only


def fixture(spec, links, routes=None):
    nodes = [{"node_id": node_id, "vertical_index": index, "vertical_band": band, "lateral_slot": lane,
              "role_modifiers": [], "resolved_role": {"status": "resolved"}} for node_id, index, band, lane in spec]
    by_id = {node["node_id"]: node for node in nodes}
    structural_links = []
    for source, target, direction in links:
        structural_links.append({"link_id": f"{source}->{target}", "source": source, "target": target, "direction": direction,
                                 "relation_type": "same_line_support" if direction == "support" else "forward_progression" if direction == "forward" else "recycle"})
    return {"nodes": nodes, "structural_links": structural_links, "progression_routes": routes or [], "role_modifiers": []}


class ProgressionEvaluatorTests(unittest.TestCase):
    def evaluate(self, item):
        qualitative = connectivity_qualitative_evaluator.evaluate_connectivity_v2(item)
        return progression_evaluator.evaluate_progression(item, qualitative)

    def test_a_connected_without_advancement(self):
        result = self.evaluate(fixture([("GK", 0, "goalkeeper", "centre"), ("CB", 1, "defensive_line", "centre")], [("GK", "CB", "support"), ("CB", "GK", "backward")]))
        self.assertEqual("interrupted", result["advancement_continuity"]["status"])
        self.assertEqual([], result["line_skips"])

    def test_b_c_d_occupied_line_gain_and_skip(self):
        staged = self.evaluate(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]))
        self.assertEqual("continuous", staged["advancement_continuity"]["status"])
        self.assertEqual(2, staged["observations"][0]["count"])
        skipped = self.evaluate(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "ST", "forward")]))
        self.assertEqual([4], skipped["line_skips"][0]["skipped_occupied_lines"])
        gap_not_skip = self.evaluate(fixture([("CB", 1, "defensive_line", "centre"), ("AM", 5, "attacking_midfield", "centre")], [("CB", "AM", "forward")]))
        self.assertEqual([], gap_not_skip["line_skips"])

    def test_e_f_g_h_regional_lateral_and_stall(self):
        left = self.evaluate(fixture([("LCB", 1, "defensive_line", "left"), ("LW", 4, "midfield", "left"), ("ST", 6, "forward", "left")], [("LCB", "LW", "forward"), ("LW", "ST", "forward")]))
        self.assertEqual("advancement_to_forward", left["regional_advancement"]["left"]["status"])
        self.assertEqual("forward", left["regional_advancement"]["left"]["highest_reachable_line"]["vertical_band"])
        self.assertEqual("no_structural_advancement", left["regional_advancement"]["centre"]["status"])
        centre = self.evaluate(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")]))
        self.assertEqual("advancement_to_forward", centre["regional_advancement"]["centre"]["status"])
        lateral_input = fixture([("L", 1, "defensive_line", "left"), ("C", 1, "defensive_line", "centre"), ("ST", 6, "forward", "centre")], [("L", "C", "support"), ("C", "ST", "forward")], [{"route_id": "lateral", "node_ids": ["L", "C", "ST"]}])
        lateral = progression_evaluator.evaluate_progression(lateral_input, {"route_diversity": {"families": [{"family_id": "lateral", "raw_route_ids": ["lateral"]}]}})
        self.assertEqual(1, lateral["route_profiles"][0]["lateral_transfers_before_advancement"])
        stalled = self.evaluate(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "CB", "backward")]))
        self.assertEqual("CM", stalled["advance_then_stall"][0]["stalled_at_position"])
        self.assertTrue(stalled["advance_then_stall"][0]["available_support_or_recycle"])

    def test_i_j_profiles_and_k_l_dependencies(self):
        base_nodes = [("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")]
        same = fixture(base_nodes, [("CB", "CM", "forward"), ("CM", "ST", "forward")], [{"route_id": "one", "node_ids": ["CB", "CM", "ST"]}, {"route_id": "two", "node_ids": ["CB", "CM", "ST"]}])
        quality = {"route_diversity": {"families": [{"family_id": "same", "raw_route_ids": ["one", "two"]}]}}
        self.assertEqual(1, len(progression_evaluator.evaluate_progression(same, quality)["route_profiles"]))
        distinct = fixture(base_nodes + [("LW", 4, "midfield", "left"), ("LST", 6, "forward", "left")], [("CB", "CM", "forward"), ("CM", "ST", "forward"), ("CB", "LW", "forward"), ("LW", "LST", "forward")], [{"route_id": "centre", "node_ids": ["CB", "CM", "ST"]}, {"route_id": "left", "node_ids": ["CB", "LW", "LST"]}])
        quality = {"route_diversity": {"families": [{"family_id": "centre", "raw_route_ids": ["centre"]}, {"family_id": "left", "raw_route_ids": ["left"]}]}}
        self.assertEqual(2, len(progression_evaluator.evaluate_progression(distinct, quality)["route_profiles"]))
        alternative = fixture(base_nodes + [("CM2", 4, "midfield", "right")], [("CB", "CM", "forward"), ("CM", "ST", "forward"), ("CB", "CM2", "forward"), ("CM2", "ST", "forward")])
        self.assertFalse(any(row["node_id"] == "CM" and "all_forward_line_access_removed" in row["proven_claims"] for row in self.evaluate(alternative)["progression_dependency"]))
        dependent = self.evaluate(fixture(base_nodes, [("CB", "CM", "forward"), ("CM", "ST", "forward")]))
        self.assertTrue(any(row["node_id"] == "CM" and "all_forward_line_access_removed" in row["proven_claims"] for row in dependent["progression_dependency"]))

    def test_pipeline_preserves_connectivity_and_adds_progression(self):
        with open("sample_leicester_4231.json", encoding="utf-8") as handle: tactic = json.load(handle)
        original = copy.deepcopy(tactic)
        report = analyze_tactic_data(tactic, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
        self.assertEqual(tactic, original)
        self.assertEqual((38, 16), (len(report["connectivity_v2"]["structural_links"]), len(report["connectivity_v2"]["progression_routes"])))
        self.assertIn("progression_evaluation", report)

    @unittest.skipUnless(os.environ.get("NODE_BINARY", "node"), "Node runner available")
    def test_python_javascript_parity_for_fixture_and_leicester(self):
        fixture_input = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")])
        with open("sample_leicester_4231.json", encoding="utf-8") as handle:
            leicester = json.load(handle)
        for input_value, expected in [(fixture_input, self.evaluate(fixture_input)), (leicester, None)]:
            if expected is None:
                report = analyze_tactic_data(input_value, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
                expected = report["progression_evaluation"]
            with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
                json.dump({"connectivity_v2": input_value} if "nodes" in input_value else input_value, handle); path = handle.name
            try:
                actual = json.loads(subprocess.check_output([os.environ.get("NODE_BINARY", "node"), "web/static/js/progression_parity_runner.mjs", path], text=True))
            finally:
                os.unlink(path)
            self.assertEqual(expected, actual)

    def test_seven_preset_regression_and_browser_parity(self):
        expected_counts = {'4-2-3-1': (38, 16), '4-3-3': (40, 48), '4-4-2': (42, 32), '4-2-4': (38, 32), '3-4-2-1': (42, 25), '3-4-3': (38, 20), '3-5-2': (48, 40)}
        for formation, expected_count in expected_counts.items():
            with self.subTest(formation=formation):
                frozen = position_only(PRESETS[formation])
                self.assertEqual(expected_count, (len(frozen["structural_links"]), len(frozen["progression_routes"])))
                expected = self.evaluate(frozen)
                with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
                    json.dump({"connectivity_v2": frozen}, handle); path = handle.name
                try:
                    actual = json.loads(subprocess.check_output([os.environ.get("NODE_BINARY", "node"), "web/static/js/progression_parity_runner.mjs", path], text=True))
                finally:
                    os.unlink(path)
                self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
