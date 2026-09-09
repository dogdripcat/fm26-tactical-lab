import copy
import json
import unittest
from pathlib import Path

import connectivity_engine
import fm26lab
import positional_relationships as positions
import role_behaviours
import role_constraints


ROOT = Path(__file__).resolve().parent


def node(position, phase="IP", role_internal_id=None):
    return positions.build_position_node(phase, position, role_internal_id)


def relations(source, target):
    return positions.calculate_configured_position_relation(node(source), node(target))["configured_position_relation"]


class ConfiguredPositionRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = positions.load_configured_position_registry()

    def test_registry_position_ids_are_unique(self):
        ids = [item["position_id"] for item in self.registry["positions"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_vertical_indexes_are_deterministic(self):
        self.assertEqual([(row["name"], row["index"]) for row in self.registry["vertical_bands"]], [
            ("goalkeeper", 0), ("defensive_line", 1), ("defensive_midfield", 2),
            ("midfield", 3), ("attacking_midfield", 4), ("forward", 5),
        ])
        self.assertEqual(node("DML")["vertical_index"], 2)
        self.assertEqual(node("AMC")["vertical_index"], 4)

    def test_lateral_slot_validation(self):
        broken = copy.deepcopy(self.registry)
        broken["positions"][0]["lateral_slot"] = "halfspace"
        with self.assertRaises(ValueError):
            positions.validate_configured_position_registry(broken)

    def test_unknown_position_fails_closed(self):
        result = positions.calculate_configured_position_relation(node("NOT_A_POSITION"), node("AMC"))
        self.assertEqual(result["configured_position_relation"]["status"], "unknown")
        self.assertEqual(result["configured_position_relation"]["relations"], [])

    def test_phase_mixing_is_not_a_relation(self):
        result = positions.calculate_configured_position_relation(node("DML", "IP"), node("AMC", "OOP"))
        self.assertEqual(result["configured_position_relation"]["status"], "invalid_phase")
        self.assertEqual(result["configured_position_relation"]["relations"], [])

    def test_dml_to_amc_is_deterministic(self):
        self.assertEqual(relations("DML", "AMC")["relations"], [
            "adjacent_lateral_slot", "wide_to_centre", "multiple_bands_forward", "forward_diagonal",
        ])

    def test_amc_to_dml_is_deterministic_reverse(self):
        self.assertEqual(relations("AMC", "DML")["relations"], [
            "adjacent_lateral_slot", "centre_to_wide", "multiple_bands_backward", "backward_diagonal",
        ])

    def test_lateral_adjacency_is_strict(self):
        self.assertIn("adjacent_lateral_slot", relations("DML", "DM")["relations"])
        self.assertIn("adjacent_lateral_slot", relations("DM", "DMR")["relations"])
        self.assertNotIn("adjacent_lateral_slot", relations("DML", "DMR")["relations"])

    def test_centre_wide_direction_is_directional(self):
        self.assertIn("centre_to_wide", relations("AMC", "AMR")["relations"])
        self.assertIn("wide_to_centre", relations("AMR", "AMC")["relations"])
        self.assertNotIn("centre_to_wide", relations("DML", "DMR")["relations"])

    def test_vertical_forward_backward_same_and_multiple(self):
        self.assertIn("one_band_forward", relations("GK", "LCB")["relations"])
        self.assertIn("one_band_backward", relations("LCB", "GK")["relations"])
        self.assertIn("same_vertical_band", relations("AMC", "AMR")["relations"])
        self.assertIn("multiple_bands_forward", relations("RB", "AMR")["relations"])

    def test_forward_and_backward_diagonal(self):
        self.assertIn("forward_diagonal", relations("DML", "AMC")["relations"])
        self.assertIn("backward_diagonal", relations("AMC", "DML")["relations"])

    def test_unknown_lateral_does_not_create_lateral_or_diagonal_relations(self):
        output = relations("CB", "DMR")["relations"]
        self.assertEqual(output, ["one_band_forward"])

    def test_expected_role_space_is_always_unknown_here(self):
        self.assertEqual(node("LB", role_internal_id="catalog:ip:wb:iwb")["expected_role_space"], {
            "status": "unknown", "items": [],
        })
        self.assertNotIn("halfspace", node("LB").values())

    def test_lcb_and_rcb_preserve_lateral_information_but_cb_does_not(self):
        self.assertEqual(node("LCB")["lateral_slot"], "left")
        self.assertEqual(node("RCB")["lateral_slot"], "right")
        self.assertEqual(node("CB")["lateral_slot"], "unknown")

    def test_edge_status_is_not_changed_by_position_relation(self):
        result = connectivity_engine.build_connectivity(
            {"ip_roles": {"DML": "DLP", "AMC": "AM"}},
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), fm26lab.ROLE_ALIASES,
        )
        edge = result["edges"][0]
        self.assertEqual(edge["status"], "connected")
        self.assertEqual(edge["configured_position_relation"]["relations"], [
            "adjacent_lateral_slot", "wide_to_centre", "multiple_bands_forward", "forward_diagonal",
        ])

    def test_position_relation_cannot_create_structural_block(self):
        result = connectivity_engine.build_connectivity(
            {"ip_roles": {"DML": "CHF", "AMC": "AM"}},
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), fm26lab.ROLE_ALIASES,
        )
        self.assertEqual(result["edges"][0]["status"], "unknown")

    def test_leicester_connectivity_regression(self):
        tactic = json.loads((ROOT / "sample_leicester_4231.json").read_text(encoding="utf-8"))
        result = connectivity_engine.build_connectivity(
            tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), fm26lab.ROLE_ALIASES,
        )
        self.assertEqual(len(result["edges"]), 61)
        self.assertEqual(result["evidence_completeness"], {
            "edges_total": 61, "semantic_complete": 2, "mixed": 7,
            "compatibility_only": 4, "evidence_missing": 48,
        })


if __name__ == "__main__":
    unittest.main()
