import copy
import json
import unittest
from pathlib import Path

import compatibility_candidates as compatibility
import connectivity_engine
import fm26lab
import role_behaviours
import role_constraints


ROOT = Path(__file__).resolve().parent


class CompatibilityCandidateRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = compatibility.load_candidate_registry()
        cls.evidence = compatibility.load_rule_evidence_registry()

    def candidate(self, candidate_id):
        return next(item for item in self.registry["candidates"] if item["candidate_id"] == candidate_id)

    def test_exactly_five_unique_candidates_are_registered(self):
        ids = [item["candidate_id"] for item in self.registry["candidates"]]
        self.assertEqual(ids, [
            "CAND_DIST_FORWARD_TO_BETWEEN_LINES", "CAND_DIST_FORWARD_TO_CENTRAL_RECEIVE",
            "CAND_SPACE_OPEN_FOR_FULLBACK_WIDE_USAGE", "CAND_FORWARD_SEND_TO_MOVE_TO_RECEIVE",
            "CAND_SIMPLE_SEND_TO_MOVE_TO_RECEIVE",
        ])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(compatibility.validate_candidate_registry(self.registry, self.evidence)["valid"])

    def test_semantic_and_ers_selectors_are_valid(self):
        result = compatibility.validate_candidate_registry(self.registry, self.evidence)
        self.assertTrue(all(item["schema_valid"] for item in result["candidates"]))
        target = self.candidate("CAND_SPACE_OPEN_FOR_FULLBACK_WIDE_USAGE")["target_selector"]
        self.assertEqual(target, {"selector_type": "ers", "field": "occupancy", "concept_id": "wide"})

    def test_invalid_semantic_and_ers_concept_are_rejected(self):
        bad_semantic = copy.deepcopy(self.registry)
        bad_semantic["candidates"][0]["source_selector"]["semantic_id"] = "not_a_semantic"
        self.assertFalse(compatibility.validate_candidate_registry(bad_semantic, self.evidence)["valid"])
        bad_ers = copy.deepcopy(self.registry)
        bad_ers["candidates"][2]["target_selector"]["concept_id"] = "not_an_ers_concept"
        self.assertFalse(compatibility.validate_candidate_registry(bad_ers, self.evidence)["valid"])

    def test_role_name_and_union_selectors_are_rejected(self):
        role_name = copy.deepcopy(self.registry)
        role_name["candidates"][0]["source_selector"] = {"selector_type": "role_name", "role_name": "인사이드 포워드"}
        self.assertFalse(compatibility.validate_candidate_registry(role_name, self.evidence)["valid"])
        union = copy.deepcopy(self.registry)
        union["candidates"][3]["source_selector"]["semantic_id"] = "send_forward | send_simple_pass"
        self.assertFalse(compatibility.validate_candidate_registry(union, self.evidence)["valid"])

    def test_invalid_phase_and_duplicate_definition_are_rejected(self):
        invalid_phase = copy.deepcopy(self.registry)
        invalid_phase["candidates"][0]["phase"] = "IP/OOP"
        self.assertFalse(compatibility.validate_candidate_registry(invalid_phase, self.evidence)["valid"])
        duplicate = copy.deepcopy(self.registry)
        duplicate["candidates"][1]["target_selector"] = copy.deepcopy(duplicate["candidates"][0]["target_selector"])
        self.assertFalse(compatibility.validate_candidate_registry(duplicate, self.evidence)["valid"])

    def test_empty_rule_evidence_registry_is_valid_and_has_zero_entries(self):
        result = compatibility.validate_rule_evidence_registry(self.evidence, {item["candidate_id"] for item in self.registry["candidates"]})
        self.assertTrue(result["valid"])
        self.assertEqual(result["evidence"], [])

    def test_unknown_rule_evidence_candidate_reference_is_rejected(self):
        evidence = {"evidence": [{
            "rule_evidence_id": "COMP_RULE_EVIDENCE_TEST_001", "source_kind": "user_ingame",
            "verification": "evidence_present", "title": "test", "source": "test", "accessed": "2026-09-08",
            "claim": "test", "supports_candidate_ids": ["CAND_UNKNOWN"], "limitations": [],
        }]}
        result = compatibility.validate_rule_evidence_registry(evidence, {item["candidate_id"] for item in self.registry["candidates"]})
        self.assertFalse(result["valid"])

    def test_all_current_candidates_are_design_only_and_not_production_eligible(self):
        report = compatibility.compatibility_candidate_readiness(self.registry, self.evidence)
        self.assertEqual((report["candidates_total"], report["rule_evidence_total"], report["production_eligible"]), (5, 0, 0))
        self.assertEqual(report["not_production_eligible"], 5)
        self.assertEqual(report["by_status"], {"design_candidate": 5})
        self.assertTrue(all(not item["production_eligible"] for item in report["candidates"]))
        self.assertTrue(all("missing_compatibility_rule_evidence" in item["blocking_reasons"] for item in report["candidates"]))

    def test_context_hypothesis_is_not_promoted_to_required_context(self):
        candidate = self.candidate("CAND_SPACE_OPEN_FOR_FULLBACK_WIDE_USAGE")
        self.assertEqual(candidate["required_context"], {"position_families": [], "configured_position_relations": []})
        self.assertEqual(candidate["candidate_context_hypothesis"], {"target_position_families": ["full_back", "wing_back"]})

    def test_verified_role_semantics_do_not_verify_candidate_rule(self):
        report = compatibility.compatibility_candidate_readiness(self.registry, self.evidence)
        item = next(item for item in report["candidates"] if item["candidate_id"] == "CAND_DIST_FORWARD_TO_BETWEEN_LINES")
        self.assertEqual(item["verified_rule_evidence_count"], 0)
        self.assertIn("candidate_not_verified_rule", item["blocking_reasons"])

    def test_registry_has_no_connectivity_effect(self):
        tactic = json.loads((ROOT / "sample_leicester_4231.json").read_text(encoding="utf-8"))
        result = connectivity_engine.build_connectivity(
            tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), fm26lab.ROLE_ALIASES,
        )
        self.assertEqual(result["evidence_completeness"], {
            "edges_total": 61, "semantic_complete": 2, "mixed": 7,
            "compatibility_only": 4, "evidence_missing": 48,
        })
        self.assertEqual([item["status"] for item in result["progression_chains"]], ["unknown_chain"] * 6)
        self.assertEqual(result["isolated_nodes"], [])


if __name__ == "__main__":
    unittest.main()
