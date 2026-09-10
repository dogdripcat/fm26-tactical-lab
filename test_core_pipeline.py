import copy
import unittest

from core.pipeline import analyze_tactic_data
import fm26lab
import role_behaviours
import role_constraints


class CorePipelineTests(unittest.TestCase):
    def test_pure_pipeline_normalizes_without_mutating_input(self):
        tactic = {"ip_roles": {"ST": "CFwd", "AMR": "WF"}, "oop_roles": {"ST": "CFwd"}}
        original = copy.deepcopy(tactic)
        report = analyze_tactic_data(
            tactic, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES,
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(),
        )
        self.assertEqual(tactic, original)
        self.assertEqual(report["normalization"]["changes"], [
            {"phase": "IP", "position": "ST", "before": "CFwd", "after": "CHF"},
            {"phase": "IP", "position": "AMR", "before": "WF", "after": "WFD"},
        ])
        self.assertIn("connectivity", report)
        self.assertTrue(all("from_node" in edge and "to_node" in edge and "connection_type" in edge for edge in report["connectivity"]["edges"]))

    def test_legacy_configured_position_alias_normalizes_without_mutating_input(self):
        tactic = {"ip_roles": {"DL": "WB", "ST": "CFD"}}
        original = copy.deepcopy(tactic)
        report = analyze_tactic_data(
            tactic, fm26lab.ROLE_DICTIONARY, fm26lab.ROLE_ALIASES,
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(),
        )
        self.assertEqual(tactic, original)
        nodes = {node["node_id"]: node for node in report["connectivity"]["nodes"]}
        self.assertIn("IP:LB", nodes)
        self.assertEqual("full_back", nodes["IP:LB"]["position_family"])


if __name__ == "__main__":
    unittest.main()
