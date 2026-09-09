import copy
import json
import unittest
from pathlib import Path

import compatibility_candidates
import evidence_request_manifest
import expected_role_space
import fm26lab
import role_behaviours
import role_constraints
import role_evidence_planning


ROOT = Path(__file__).resolve().parent


class RoleEvidencePlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tactic = json.loads((ROOT / "sample_leicester_4231.json").read_text(encoding="utf-8"))
        cls.catalog = role_constraints.load_role_catalog()
        cls.knowledge = role_behaviours.load_knowledge_base()
        cls.plan = role_evidence_planning.build_role_evidence_collection_plan(
            cls.tactic, cls.catalog, cls.knowledge, fm26lab.ROLE_ALIASES,
        )

    def role(self, internal_id):
        return next(item for item in self.plan["leicester_roles"] if item["role_internal_id"] == internal_id)

    def test_leicester_resolves_all_eleven_ip_roles(self):
        self.assertEqual(self.plan["leicester_ip_resolution"], {
            "configured_roles": 11, "resolved_roles": 11, "unresolved_roles": 0,
            "resolved_node_ids": ["IP:GK", "IP:LB", "IP:LCB", "IP:RCB", "IP:RB", "IP:DML", "IP:DMR", "IP:AML", "IP:AMC", "IP:AMR", "IP:ST"],
        })

    def test_edge_exposure_preserves_source_target_and_completeness(self):
        dlp = self.role("catalog:ip:dm:dlp")["source_target_edge_exposure"]
        self.assertEqual(dlp["source"], {"semantic_complete": 2, "mixed": 2, "compatibility_only": 0, "evidence_missing": 1})
        self.assertEqual(dlp["target"], {"semantic_complete": 0, "mixed": 0, "compatibility_only": 0, "evidence_missing": 7})

    def test_shared_centre_back_identity_is_preserved(self):
        cb = self.role("catalog:ip:centre-back:cb")
        self.assertTrue(cb["shared_role_identity"])
        self.assertEqual(cb["configured_nodes"], ["IP:LCB", "IP:RCB"])
        self.assertEqual(cb["source_target_edge_exposure"]["source"]["evidence_missing"], 12)

    def test_role_rows_include_behaviour_semantic_ers_and_gap_data(self):
        row = self.role("catalog:ip:fw:cfd")
        self.assertEqual(row["behaviour_coverage"], "partial")
        self.assertEqual(row["ers_status"], "unknown")
        self.assertIn("target evidence_missing edge에 대응하는 edge-eligible receive semantic 근거 없음", row["evidence_gaps"])

    def test_categorical_tiers_and_screenshot_batches(self):
        self.assertEqual(self.plan["priority_tiers"]["A"], [
            "catalog:ip:centre-back:cb", "catalog:ip:fw:cfd", "catalog:ip:goalkeeper:bgk",
        ])
        self.assertEqual(len(self.plan["priority_tiers"]["B"]), 7)
        self.assertEqual(self.plan["screenshot_batches"]["batch_1"]["role_internal_ids"], self.plan["priority_tiers"]["A"])
        self.assertEqual(self.plan["screenshot_batches"]["batch_3"]["role_internal_ids"], self.plan["priority_tiers"]["C"])

    def test_tiers_do_not_use_a_core_line_family_constant(self):
        self.assertFalse(hasattr(role_evidence_planning, "CORE_FAMILIES"))
        self.assertEqual(self.role("catalog:ip:centre-back:cb")["priority_tier"], "A")
        self.assertTrue(self.role("catalog:ip:centre-back:cb")["shared_role_identity"])

    def test_oop_and_global_coverage_are_read_from_current_data(self):
        self.assertEqual(self.plan["oop_gap"]["coverage"], {"identity_only": 32})
        global_coverage = self.plan["global_coverage"]
        self.assertEqual(global_coverage["roles_total"], 69)
        self.assertEqual(global_coverage["behaviour_status_totals"], {"verified": 0, "partial": 10, "identity_only": 57, "unresolved": 2})
        self.assertEqual(global_coverage["ers_coverage"]["supported"], 7)

    def test_planning_does_not_mutate_inputs_or_coverage(self):
        tactic, catalog, knowledge = copy.deepcopy(self.tactic), copy.deepcopy(self.catalog), copy.deepcopy(self.knowledge)
        before_ers = expected_role_space.expected_role_space_coverage(catalog, knowledge)
        role_evidence_planning.build_role_evidence_collection_plan(tactic, catalog, knowledge, fm26lab.ROLE_ALIASES)
        self.assertEqual(tactic, self.tactic)
        self.assertEqual(catalog, self.catalog)
        self.assertEqual(knowledge, self.knowledge)
        self.assertEqual(expected_role_space.expected_role_space_coverage(catalog, knowledge), before_ers)

    def test_connectivity_and_compatibility_readiness_regressions_are_unchanged(self):
        snapshot = self.plan["connectivity_regression_snapshot"]
        self.assertEqual((snapshot["edges"], snapshot["semantic_complete"], snapshot["mixed"], snapshot["compatibility_only"], snapshot["evidence_missing"]), (61, 2, 7, 4, 48))
        self.assertEqual(snapshot["progression_chain_statuses"], {"unknown_chain": 6})
        self.assertEqual(snapshot["isolated_nodes"], 0)
        readiness = compatibility_candidates.compatibility_candidate_readiness()
        self.assertEqual((readiness["candidates_total"], readiness["production_eligible"]), (5, 0))

    def test_evidence_request_manifest_reports_existing_evidence_before_requests(self):
        manifest = evidence_request_manifest.build_evidence_request_manifest(
            self.tactic, self.catalog, self.knowledge, fm26lab.ROLE_ALIASES,
        )
        self.assertEqual(len(manifest["roles"]), 10)
        by_id = {item["role_internal_id"]: item for item in manifest["roles"]}
        cb = by_id["catalog:ip:centre-back:cb"]
        self.assertEqual(cb["existing_evidence_ids"], ["USER_FM26_IP_CB_DESCRIPTION_001"])
        self.assertEqual([item["semantic_id"] for item in cb["existing_semantics"]], ["send_simple_pass"])
        self.assertIn("send_simple_pass != send_forward", cb["do_not_reinfer"])
        self.assertTrue(cb["recheck_existing_evidence_first"])
        self.assertFalse(cb["additional_capture"]["required"])
        self.assertIn("CB_IP_HOLD_POSITION", [item["behaviour_id"] for item in cb["existing_supported_claims"]])
        self.assertIn("CB_IP_SUPPORT_POSSESSION", [item["behaviour_id"] for item in cb["existing_supported_claims"]])
        bgk = by_id["catalog:ip:goalkeeper:bgk"]
        self.assertIn("move_to_receive != receive", bgk["do_not_reinfer"])
        self.assertIn("active buildup participation != specific distribution target", bgk["do_not_reinfer"])
        cfd = by_id["catalog:ip:fw:cfd"]
        self.assertIn("CFD_IP_ATTACKING_FOCAL_POINT", [item["behaviour_id"] for item in cfd["existing_supported_claims"]])
        self.assertIn("attacking focal point != receive_centrally", cfd["do_not_reinfer"])
        self.assertIn("target reception evidence unavailable", cfd["missing_analysis_evidence"]["analysis_gap"])
        self.assertIn("current evidence does not explicitly establish receiving behaviour", cfd["missing_analysis_evidence"]["evidence_claim_missing"])

    def test_manifest_preserves_current_oop_input_without_resolving_sk(self):
        manifest = evidence_request_manifest.build_evidence_request_manifest(
            self.tactic, self.catalog, self.knowledge, fm26lab.ROLE_ALIASES,
        )
        self.assertEqual(manifest["leicester_oop_input"]["raw_roles"], {"GK": "SK"})
        self.assertEqual(manifest["leicester_oop_input"]["resolved_roles"], 0)


if __name__ == "__main__":
    unittest.main()
