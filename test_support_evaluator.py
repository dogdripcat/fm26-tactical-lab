"""Support Phase 1 fixtures: continuation categories are structural, never scores."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import connectivity_qualitative_evaluator
import progression_evaluator
import support_evaluator
from core.pipeline import analyze_tactic_data
import fm26lab
import role_behaviours
import role_constraints
from test_connectivity_engine_v2 import PRESETS, position_only

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "web" / "static" / "js" / "support_parity_runner.mjs"


def fixture(nodes, links, routes=None):
    result_nodes = [{"node_id": node_id, "configured_position": node_id.split(":")[-1],
                     "vertical_index": index, "vertical_band": band, "lateral_slot": region,
                     "role_modifiers": [], "resolved_role": {"status": "resolved"}}
                    for node_id, index, band, region in nodes]
    result_links = []
    for source, target, direction in links:
        result_links.append({"link_id": f"{source}->{target}", "source": source, "target": target,
                             "direction": direction,
                             "relation_type": "same_line_support" if direction == "support" else "recycle" if direction == "backward" else "forward_progression"})
    return {"nodes": result_nodes, "structural_links": result_links,
            "progression_routes": routes or [], "role_modifiers": []}


def evaluate(v2):
    quality = connectivity_qualitative_evaluator.evaluate_connectivity_v2(v2)
    return progression_evaluator.evaluate_progression(v2, quality), support_evaluator.evaluate_support(v2, progression_evaluator.evaluate_progression(v2, quality))


class SupportEvaluatorTests(unittest.TestCase):
    def profile(self, v2, receiver):
        return next(row for row in evaluate(v2)[1]["receiving_states"] if row["receiver_id"] == receiver)

    def test_a_to_d_direction_categories_and_single_option_are_descriptive(self):
        v2 = fixture(
            [("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"),
             ("ML", 4, "midfield", "left"), ("DM", 3, "defensive_midfield", "centre"), ("ST", 6, "forward", "centre")],
            [("CB", "CM", "forward"), ("CM", "ST", "forward"), ("CM", "ML", "support"), ("CM", "DM", "backward")],
        )
        row = self.profile(v2, "CM")
        self.assertEqual(["forward", "lateral", "recycle"], row["support_directions"])
        self.assertFalse(row["single_option_support"])
        recycle_only = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("DM", 3, "defensive_midfield", "centre")], [("CB", "CM", "forward"), ("CM", "DM", "backward")]), "CM")
        lateral_only = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ML", 4, "midfield", "left")], [("CB", "CM", "forward"), ("CM", "ML", "support")]), "CM")
        self.assertEqual(["recycle"], recycle_only["support_directions"])
        self.assertEqual(["lateral"], lateral_only["support_directions"])
        self.assertTrue(lateral_only["support_options"]["outside"])
        self.assertTrue(lateral_only["single_option_support"])

    def test_e_f_terminal_and_nonterminal_isolation_are_distinct(self):
        terminal = fixture([("GK", 0, "goalkeeper", "centre"), ("ST", 6, "forward", "centre")], [("GK", "ST", "forward")], [{"route_id": "GK->ST", "node_ids": ["GK", "ST"]}])
        terminal_row = self.profile(terminal, "ST")
        self.assertTrue(terminal_row["terminal_endpoint"])
        self.assertFalse(terminal_row["support_isolated"])
        two = fixture([("GK", 0, "goalkeeper", "centre"), ("CF", 6, "forward", "left"), ("ST", 6, "forward", "right")], [("GK", "CF", "forward"), ("GK", "ST", "forward")], [{"route_id": "GK->CF", "node_ids": ["GK", "CF"]}, {"route_id": "GK->ST", "node_ids": ["GK", "ST"]}])
        self.assertTrue(self.profile(two, "CF")["terminal_endpoint"])
        self.assertTrue(self.profile(two, "ST")["terminal_endpoint"])
        isolated = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre")], [("CB", "CM", "forward")]), "CM")
        self.assertFalse(isolated["terminal_endpoint"])
        self.assertTrue(isolated["support_isolated"])

    def test_terminal_edge_cases_and_primary_direction_overlap_are_deterministic(self):
        # A configured forward-band endpoint may have lateral, recycle, or no continuation.
        wide = fixture([("CB", 1, "defensive_line", "centre"), ("WFD", 6, "forward", "left"), ("ST", 6, "forward", "centre"), ("DM", 3, "defensive_midfield", "centre")], [("CB", "WFD", "forward"), ("WFD", "ST", "support"), ("WFD", "DM", "backward")], [{"route_id": "CB->WFD", "node_ids": ["CB", "WFD"]}])
        wide_row = self.profile(wide, "WFD")
        self.assertTrue(wide_row["terminal_endpoint"])
        self.assertEqual(["lateral", "recycle"], wide_row["support_directions"])
        # The same lateral edge also has an inside relation, but counts once as a primary direction.
        one_target = self.profile(fixture([("CB", 1, "defensive_line", "left"), ("W", 4, "midfield", "left"), ("C", 4, "midfield", "centre")], [("CB", "W", "forward"), ("W", "C", "support")]), "W")
        self.assertEqual(["lateral"], one_target["support_directions"])
        self.assertTrue(one_target["support_options"]["inside"])
        self.assertTrue(one_target["single_option_support"])
        # A highest line with a non-forward band is not a terminal attacker.
        highest_cm = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre")], [("CB", "CM", "forward")]), "CM")
        self.assertFalse(highest_cm["terminal_endpoint"])
        self.assertTrue(highest_cm["support_isolated"])

    def test_receivers_are_inbound_or_route_intermediates_and_never_phantom(self):
        v2 = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre"), ("UNUSED", 4, "midfield", "left")], [("CB", "CM", "forward"), ("CM", "ST", "forward")], [{"route_id": "CB->CM->ST", "node_ids": ["CB", "CM", "ST"]}])
        _, support = evaluate(v2)
        self.assertEqual(["CM", "ST"], [row["receiver_id"] for row in support["receiving_states"]])
        self.assertTrue(all(row["inbound_structural_context"] for row in support["receiving_states"]))
        self.assertNotIn("UNUSED", [row["receiver_id"] for row in support["receiving_states"]])

    def test_g_to_n_advance_context_cross_region_and_shared_connector_boundaries(self):
        v2 = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ML", 4, "midfield", "left"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ML", "support"), ("CM", "ST", "forward")], [{"route_id": "CB->CM->ST", "node_ids": ["CB", "CM", "ST"]}])
        progression, support = evaluate(v2)
        self.assertTrue(any(row["receiver_id"] == "CM" and row["forward_continuation"] and row["lateral_continuation"] for row in support["advance_then_support"]))
        self.assertTrue(any(row["dependent_receiver"] == "CM" and row["support_node"] == "ML" and "lateral" in row["lost_support_categories"] for row in support["support_dependencies"]))
        self.assertTrue(support["regional_support"]["centre"]["cross_region_support_available"])
        # A shared route connector has no automatic Support dependency unless a continuation category is lost.
        shared = fixture([("A", 1, "defensive_line", "left"), ("B", 1, "defensive_line", "right"), ("C", 4, "midfield", "centre"), ("D", 6, "forward", "centre"), ("E", 4, "midfield", "left")], [("A", "C", "forward"), ("B", "C", "forward"), ("C", "D", "forward"), ("C", "E", "support")], [{"route_id": "A->C->D", "node_ids": ["A", "C", "D"]}, {"route_id": "B->C->D", "node_ids": ["B", "C", "D"]}])
        self.assertFalse(any(row["support_node"] == "C" for row in evaluate(shared)[1]["support_dependencies"]))
        self.assertEqual([], progression["advance_then_stall"])

    def test_o_to_q_never_inherit_other_dependency_labels_and_prove_removal(self):
        v2 = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ML", 4, "midfield", "left"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ML", "support"), ("CM", "ST", "forward")])
        progression, support = evaluate(v2)
        progression["progression_dependency"] = [{"node_id": "CM", "proven_claims": ["all_forward_line_access_removed"]}]
        again = support_evaluator.evaluate_support(v2, progression)
        self.assertTrue(any(row["support_node"] == "ML" and row["becomes_support_isolated"] is False for row in again["support_dependencies"]))
        self.assertFalse(any(row["support_node"] == "CM" for row in again["support_dependencies"]))
        only = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")])
        self.assertTrue(any(row["dependent_receiver"] == "CM" and row["support_node"] == "ST" and row["becomes_support_isolated"] for row in evaluate(only)[1]["support_dependencies"]))

    def test_role_adjustments_and_pipeline_are_additive(self):
        with open(ROOT / "sample_leicester_4231.json", encoding="utf-8") as handle:
            tactic = json.load(handle)
        original = copy.deepcopy(tactic)
        report = analyze_tactic_data(tactic, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES,
                                     role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
        self.assertEqual(tactic, original)
        self.assertIn("support_evaluation", report)
        self.assertEqual((38, 16), (len(report["connectivity_v2"]["structural_links"]), len(report["connectivity_v2"]["progression_routes"])))
        self.assertTrue(any(row["semantic_id"] == "send_forward" for row in report["support_evaluation"]["role_adjustments"]))
        self.assertNotIn("score", json.dumps(report["support_evaluation"]))

    def test_direction_reversal_and_malformed_direction_labels_do_not_create_support(self):
        # CB→CM proves CM can receive, but gives no post-reception option from CM.
        only_inbound = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre")], [("CB", "CM", "forward")]), "CM")
        self.assertEqual([], only_inbound["support_directions"])
        # Labels alone cannot turn same/deeper lines into forward support.
        malformed = self.profile(fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("SAME", 4, "midfield", "left"), ("DEEP", 1, "defensive_line", "centre")], [("CB", "CM", "forward"), ("CM", "SAME", "forward"), ("CM", "DEEP", "forward")]), "CM")
        self.assertEqual([], malformed["support_directions"])

    @unittest.skipUnless(os.environ.get("NODE_BINARY", "node"), "Node runner available")
    def test_python_javascript_parity_for_synthetic_presets_and_leicester(self):
        synthetic = fixture([("CB", 1, "defensive_line", "centre"), ("CM", 4, "midfield", "centre"), ("ST", 6, "forward", "centre")], [("CB", "CM", "forward"), ("CM", "ST", "forward")])
        inputs = [synthetic] + [position_only(positions) for positions in PRESETS.values()]
        with open(ROOT / "sample_leicester_4231.json", encoding="utf-8") as handle:
            leicester = json.load(handle)
        for value in inputs + [leicester]:
            if "nodes" in value:
                quality = connectivity_qualitative_evaluator.evaluate_connectivity_v2(value)
                progression = progression_evaluator.evaluate_progression(value, quality)
                expected = support_evaluator.evaluate_support(value, progression)
                payload = {"connectivity_v2": value, "progression_evaluation": progression}
            else:
                report = analyze_tactic_data(value, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES,
                                             role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
                expected = report["support_evaluation"]
                payload = value
            with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
                json.dump(payload, handle); path = handle.name
            try:
                actual = json.loads(subprocess.check_output([os.environ.get("NODE_BINARY", "node"), str(RUNNER), path], text=True, encoding="utf-8"))
            finally:
                os.unlink(path)
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
