import copy
import json
import unittest
from pathlib import Path

import compatibility_candidates
import connectivity_engine
import current_tactic_evidence_sufficiency as sufficiency
import expected_role_space
import fm26lab
import role_behaviours
import role_constraints


ROOT = Path(__file__).resolve().parent


class CurrentTacticEvidenceSufficiencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tactic = json.loads((ROOT / "sample_leicester_4231.json").read_text(encoding="utf-8"))
        cls.catalog = role_constraints.load_role_catalog()
        cls.knowledge = role_behaviours.load_knowledge_base()
        cls.report = sufficiency.build_current_tactic_evidence_sufficiency(
            cls.tactic, cls.catalog, cls.knowledge, fm26lab.ROLE_ALIASES,
        )

    def role(self, role_id):
        return next(item for item in self.report["roles"] if item["role_internal_id"] == role_id)

    def test_reports_all_eleven_resolved_ip_roles(self):
        self.assertEqual(len(self.report["roles"]), 10)  # 11 nodes; CB is one shared role identity.
        self.assertEqual(self.role("catalog:ip:centre-back:cb")["configured_positions"], ["LCB", "RCB"])

    def test_dlp_am_if_and_wfd_capabilities_follow_existing_semantics_and_ers(self):
        self.assertEqual(self.role("catalog:ip:dm:dlp")["safe_analysis_capabilities"], [
            "can_support_distribution_analysis", "can_support_space_occupation_analysis",
        ])
        self.assertIn("can_support_reception_analysis", self.role("catalog:ip:am:am")["safe_analysis_capabilities"])
        self.assertEqual(set(self.role("catalog:ip:winger:if")["safe_analysis_capabilities"]), {
            "can_support_movement_behaviour_analysis", "can_support_reception_analysis", "can_support_structural_support_analysis",
        })
        self.assertIn("can_support_space_occupation_analysis", self.role("catalog:ip:winger:wfd")["safe_analysis_capabilities"])

    def test_cb_bgk_and_cfd_remain_limited_without_edge_inference(self):
        cb = self.role("catalog:ip:centre-back:cb")
        self.assertEqual(cb["safe_analysis_capabilities"], ["can_support_generic_possession_support_analysis"])
        self.assertIn("send_simple_pass_does_not_support_connectivity_edge_inference", cb["unsafe_inferences"])
        bgk = self.role("catalog:ip:goalkeeper:bgk")
        self.assertIn("can_support_movement_behaviour_analysis", bgk["safe_analysis_capabilities"])
        self.assertIn("move_to_receive_does_not_support_connectivity_edge_inference", bgk["unsafe_inferences"])
        cfd = self.role("catalog:ip:fw:cfd")
        self.assertIn("can_support_goal_threat_behavioural_analysis", cfd["safe_analysis_capabilities"])
        self.assertIn("cannot_infer_connectivity_reception", cfd["unsafe_inferences"])

    def test_aggregate_lists_are_evidence_based(self):
        aggregate = self.report["aggregate"]
        self.assertEqual(aggregate["distribution_capable_roles"], ["catalog:ip:dm:dlp"])
        self.assertEqual(aggregate["reception_capable_roles"], ["catalog:ip:am:am", "catalog:ip:winger:if"])
        self.assertEqual(aggregate["roles_with_no_edge_eligible_connectivity_semantic"], [
            "catalog:ip:centre-back:cb", "catalog:ip:fw:cfd", "catalog:ip:goalkeeper:bgk",
        ])

    def test_report_is_read_only_and_preserves_regressions(self):
        tactic, catalog, knowledge = copy.deepcopy(self.tactic), copy.deepcopy(self.catalog), copy.deepcopy(self.knowledge)
        before_ers = expected_role_space.expected_role_space_coverage(catalog, knowledge)
        sufficiency.build_current_tactic_evidence_sufficiency(tactic, catalog, knowledge, fm26lab.ROLE_ALIASES)
        self.assertEqual(tactic, self.tactic)
        self.assertEqual(catalog, self.catalog)
        self.assertEqual(knowledge, self.knowledge)
        self.assertEqual(expected_role_space.expected_role_space_coverage(catalog, knowledge), before_ers)
        graph = connectivity_engine.build_connectivity(tactic, catalog, knowledge, fm26lab.ROLE_ALIASES)
        self.assertEqual(graph["evidence_completeness"], {
            "edges_total": 61, "semantic_complete": 2, "mixed": 7,
            "compatibility_only": 4, "evidence_missing": 48,
        })
        self.assertEqual(compatibility_candidates.compatibility_candidate_readiness()["production_eligible"], 0)


if __name__ == "__main__":
    unittest.main()
