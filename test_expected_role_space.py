import json
import unittest
from pathlib import Path

import connectivity_engine
import expected_role_space as ers
import fm26lab
import role_behaviours
import role_constraints


ROOT = Path(__file__).resolve().parent


class ExpectedRoleSpaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = role_constraints.load_role_catalog()
        cls.kb = role_behaviours.load_knowledge_base()

    def role(self, suffix):
        return next(item for item in self.catalog if item["internal_id"].endswith(":" + suffix))

    def space(self, suffix):
        role = self.role(suffix)
        return ers.build_expected_role_space(role["internal_id"], role["phase"], self.catalog, self.kb)["expected_role_space"]

    def concept_ids(self, space, field):
        return [item["concept_id"] for item in space[field]]

    def all_semantic_ids(self, space):
        return {item["semantic_id"] for field in ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions") for item in space[field]}

    def test_dlp_occupancy(self):
        result = self.space("dlp")
        self.assertEqual(self.concept_ids(result, "occupancy"), ["between_defence_and_midfield"])

    def test_am_reception_space_not_occupancy(self):
        result = self.space("am")
        self.assertEqual(self.concept_ids(result, "reception_spaces"), ["between_lines"])
        self.assertEqual(result["occupancy"], [])

    def test_if_reception_movement_and_structural_effect_are_separate(self):
        result = self.space("if")
        self.assertEqual(self.concept_ids(result, "reception_spaces"), ["central"])
        self.assertEqual(self.concept_ids(result, "movement_targets"), ["halfspace"])
        self.assertEqual(self.concept_ids(result, "structural_effects"), ["open_space_for_fullback"])
        self.assertEqual(result["occupancy"], [])

    def test_wfd_occupancy_and_movement_are_separate(self):
        result = self.space("wfd")
        self.assertEqual(self.concept_ids(result, "occupancy"), ["wide"])
        self.assertEqual(self.concept_ids(result, "movement_targets"), ["in_behind", "box"])

    def test_wb_occupancy_and_structural_effect_are_separate(self):
        result = self.space("wb")
        self.assertEqual(self.concept_ids(result, "occupancy"), ["wide"])
        self.assertEqual(self.concept_ids(result, "structural_effects"), ["buildup_line_alignment"])

    def test_iwb_direction_structural_effect_and_exclusions_are_separate(self):
        result = self.space("iwb")
        self.assertEqual(self.concept_ids(result, "movement_directions"), ["inside"])
        self.assertEqual(self.concept_ids(result, "structural_effects"), ["support_central_passing_links"])
        self.assertEqual(set(self.concept_ids(result, "exclusions")), {"byline_activity", "overlapping_attack"})
        self.assertEqual(result["occupancy"], [])
        self.assertEqual(result["movement_targets"], [])

    def test_bgk_cb_and_cfd_remain_unknown(self):
        for suffix in ("bgk", "cb", "cfd"):
            self.assertEqual(self.space(suffix)["status"], "unknown")

    def test_send_and_destinationless_movement_semantics_create_no_ers_item(self):
        self.assertNotIn("send_forward", self.all_semantic_ids(self.space("dlp")))
        self.assertNotIn("send_simple_pass", self.all_semantic_ids(self.space("cb")))
        self.assertNotIn("move_to_receive", self.all_semantic_ids(self.space("bgk")))

    def test_move_inside_does_not_become_central_or_halfspace_target(self):
        result = self.space("iwb")
        self.assertNotIn("central", self.concept_ids(result, "occupancy"))
        self.assertNotIn("halfspace", self.concept_ids(result, "movement_targets"))

    def test_exclusions_do_not_create_positive_opposites(self):
        result = self.space("iwb")
        self.assertNotIn("central", self.concept_ids(result, "occupancy"))
        self.assertNotIn("hold_position", self.concept_ids(result, "structural_effects"))

    def test_every_generated_item_has_provenance(self):
        for suffix in ("dlp", "am", "if", "wfd", "wb", "iwb"):
            result = self.space(suffix)
            for field in ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions"):
                for item in result[field]:
                    self.assertTrue(item["concept_id"] and item["semantic_id"] and item["behaviour_ids"] and item["evidence_ids"])
                    self.assertIn(item["verification"], {"official", "user_ingame_verified", "verified"})

    def test_unknown_role_and_phase_mismatch_fail_closed(self):
        unknown = ers.build_expected_role_space("catalog:ip:missing:role", "IP", self.catalog, self.kb)
        self.assertEqual(unknown["expected_role_space"]["status"], "unknown")
        with self.assertRaises(ValueError):
            ers.build_expected_role_space(self.role("dlp")["internal_id"], "OOP", self.catalog, self.kb)

    def test_configured_position_context_is_preserved(self):
        result = ers.build_position_context_with_expected_role_space(
            "IP", "LB", self.role("iwb")["internal_id"], self.catalog, self.kb,
        )
        self.assertEqual(result["configured_position_context"], {
            "configured_position": "LB", "position_family": "full_back", "vertical_band": "defensive_line",
            "vertical_index": 1, "lateral_slot": "left",
        })
        self.assertEqual(result["expected_role_space"]["movement_directions"][0]["concept_id"], "inside")

    def test_coverage_and_unmapped_semantics_are_calculated(self):
        coverage = ers.expected_role_space_coverage(self.catalog, self.kb)
        self.assertEqual((coverage["roles_total"], coverage["supported"], coverage["unknown"]), (69, 7, 62))
        self.assertEqual(coverage["by_field"], {
            "occupancy": 3, "reception_spaces": 2, "movement_targets": 4, "movement_directions": 1,
            "structural_effects": 3, "exclusions": 2,
        })
        self.assertEqual([item["semantic_id"] for item in coverage["unmapped_semantics"]], [
            "send_forward", "send_simple_pass", "move_to_receive",
        ])

    def test_connectivity_regression_is_unchanged(self):
        tactic = json.loads((ROOT / "sample_leicester_4231.json").read_text(encoding="utf-8"))
        result = connectivity_engine.build_connectivity(tactic, self.catalog, self.kb, fm26lab.ROLE_ALIASES)
        self.assertEqual(result["evidence_completeness"], {
            "edges_total": 61, "semantic_complete": 2, "mixed": 7,
            "compatibility_only": 4, "evidence_missing": 48,
        })
        self.assertEqual([item["status"] for item in result["progression_chains"]], ["unknown_chain"] * 6)
        self.assertEqual(result["isolated_nodes"], [])


if __name__ == "__main__":
    unittest.main()
