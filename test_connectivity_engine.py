import copy
import unittest

import connectivity_engine as engine
import role_behaviours
import role_constraints


def catalog_role(internal_id, abbr, ref):
    return {
        "internal_id": internal_id, "phase": "IP",
        "role_families": ["test"],
        "available_starting_positions": [], "available_starting_positions_verification": "unknown",
        "role_name_ko": internal_id, "role_name_en": None,
        "display_abbr": abbr, "display_abbr_verification": "user_ingame_verified",
        "name_verified": True, "role_behaviour_ref": {"phase": "IP", "role": ref},
        "evidence": [], "formation_constraints": [],
    }


def behaviour(role, category, verification="user_ingame_verified"):
    return {
        "role": role, "phase": "IP", "behaviour_verified": True,
        "relationships": [],
        "evidence": [{"evidence_id": role + "_E", "source_type": "user_ingame_capture", "title": role, "source": "test:" + role, "accessed": "2026-09-08", "notes": "test"}],
        "behaviours": [{"behaviour_id": role + "_B", "category": category, "claim": role, "conditions": ["in_possession"], "evidence_ids": [role + "_E"], "verification": verification}],
    }


class ConnectivityTests(unittest.TestCase):
    def test_directional_verified_candidate(self):
        result = engine.build_connectivity(
            {"ip_roles": {"DML": "DLP", "AMC": "AM", "ST": "CFD"}},
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), {},
        )
        edges = {edge["edge_id"]: edge for edge in result["edges"]}
        self.assertEqual(edges["IP:DML->IP:AMC"]["status"], "connected")
        self.assertEqual(edges["IP:DML->IP:AMC"]["path_type"], "midfield_to_attacking_midfield")
        self.assertNotIn("IP:AMC->IP:DML", edges)
        self.assertTrue(edges["IP:DML->IP:AMC"]["source_basis"])
        self.assertTrue(edges["IP:DML->IP:AMC"]["target_basis"])
        provenance = edges["IP:DML->IP:AMC"]["provenance"]
        self.assertEqual(provenance["evidence_completeness"], "semantic_complete")
        self.assertEqual(provenance["semantic_ids"], ["receive_between_lines", "send_forward"])
        self.assertIn("DLP_IP_FORWARD_PASSES", provenance["behaviour_ids"])
        self.assertIn("USER_FM26_AM_DESCRIPTION", provenance["evidence_ids"])

    def test_ip_only_and_unresolved_is_unknown(self):
        result = engine.build_connectivity(
            {"ip_roles": {"DML": "NOT_A_ROLE", "AMC": "AM"}, "oop_roles": {"DML": "DLP"}},
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), {},
        )
        self.assertEqual([node["phase"] for node in result["nodes"]], ["IP", "IP"])
        self.assertEqual(result["nodes"][0]["resolved_role"]["status"], "unresolved")
        self.assertEqual(result["edges"][0]["status"], "unknown")

    def test_unknown_and_explicit_structural_block_are_distinct(self):
        catalog = [catalog_role("test:def", "DEF", "DEF"), catalog_role("test:mid", "MID", "MID"), catalog_role("test:am", "ATK", "ATK"), catalog_role("test:fwd", "FWD", "FWD")]
        knowledge = [behaviour("DEF", "goal_threat"), behaviour("MID", "goal_threat"), behaviour("ATK", "ball_receiving"), behaviour("FWD", "ball_receiving")]
        unknown_by_absence = engine.build_connectivity({"ip_roles": {"LCB": "DEF", "DML": "MID", "AMC": "ATK", "ST": "FWD"}}, catalog, knowledge, {})
        self.assertEqual(unknown_by_absence["edges"][0]["status"], "unknown")
        self.assertEqual(unknown_by_absence["progression_chains"][0]["status"], "unknown_chain")
        blocked = copy.deepcopy(knowledge)
        blocked[0]["behaviours"][0]["connectivity_effect"] = "structurally_unsupported"
        blocked[0]["behaviours"][0]["connection_types"] = ["defence_to_midfield"]
        broken = engine.build_connectivity({"ip_roles": {"LCB": "DEF", "DML": "MID", "AMC": "ATK", "ST": "FWD"}}, catalog, blocked, {})
        self.assertEqual(broken["edges"][0]["status"], "structurally_unsupported")
        self.assertEqual(broken["progression_chains"][0]["status"], "broken_progression_chain")
        missing = copy.deepcopy(knowledge)
        missing[1]["behaviours"] = []
        missing[1]["behaviour_verified"] = False
        unknown = engine.build_connectivity({"ip_roles": {"LCB": "DEF", "DML": "MID", "AMC": "ATK", "ST": "FWD"}}, catalog, missing, {})
        self.assertEqual(unknown["edges"][0]["status"], "unknown")
        self.assertEqual(unknown["progression_chains"][0]["status"], "unknown_chain")

    def test_isolated_node_and_unverified_behaviour_blocked(self):
        catalog = [catalog_role("test:mid", "MID", "MID"), catalog_role("test:am", "ATK", "ATK")]
        knowledge = [behaviour("MID", "passing", "unverified"), behaviour("ATK", "ball_receiving")]
        knowledge[0]["behaviour_verified"] = False
        result = engine.build_connectivity({"ip_roles": {"DML": "MID", "AMC": "ATK"}}, catalog, knowledge, {})
        self.assertEqual(result["edges"][0]["status"], "unknown")
        self.assertEqual(result["isolated_nodes"][0]["status"], "unknown")
        self.assertTrue(all(not node.get("described_behaviours") for node in result["nodes"] if node["configured_position"] == "DML"))

    def test_provenance_mixed_compatibility_only_and_evidence_missing(self):
        catalog = role_constraints.load_role_catalog()
        knowledge = role_behaviours.load_knowledge_base()
        mixed = engine.build_connectivity({"ip_roles": {"DML": "DLP", "RB": "IWB"}}, catalog, knowledge, {})["edges"][0]
        self.assertEqual(mixed["provenance"]["source_method"], "semantic")
        self.assertEqual(mixed["provenance"]["target_method"], "compatibility")
        self.assertEqual(mixed["provenance"]["evidence_completeness"], "mixed")
        compatibility_catalog = [catalog_role("test:def", "DEF", "DEF"), catalog_role("test:mid", "MID", "MID")]
        compatibility_kb = [behaviour("DEF", "passing"), behaviour("MID", "ball_receiving")]
        compatibility = engine.build_connectivity({"ip_roles": {"LCB": "DEF", "DML": "MID"}}, compatibility_catalog, compatibility_kb, {})["edges"][0]
        self.assertEqual(compatibility["provenance"]["evidence_completeness"], "compatibility_only")
        missing = engine.build_connectivity({"ip_roles": {"DML": "CHF", "AMC": "AM"}}, catalog, knowledge, {})["edges"][0]
        self.assertEqual(missing["provenance"]["evidence_completeness"], "evidence_missing")

    def test_provenance_summary_is_not_an_edge_score(self):
        result = engine.build_connectivity(
            {"ip_roles": {"DML": "DLP", "AMC": "AM", "RB": "IWB"}},
            role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), {},
        )
        summary = result["evidence_completeness"]
        self.assertEqual(summary["edges_total"], len(result["edges"]))
        self.assertEqual(sum(summary[key] for key in ("semantic_complete", "mixed", "compatibility_only", "evidence_missing")), summary["edges_total"])

    def test_semantic_provenance_does_not_change_existing_edge_status(self):
        tactic = {"ip_roles": {"DML": "DLP", "AMC": "AM", "RB": "IWB"}}
        catalog = role_constraints.load_role_catalog()
        knowledge = role_behaviours.load_knowledge_base()
        with_semantics = engine.build_connectivity(tactic, catalog, knowledge, {})
        without_semantics = copy.deepcopy(knowledge)
        for entry in without_semantics:
            for item in entry["behaviours"]:
                item.pop("connectivity_semantics", None)
        legacy = engine.build_connectivity(tactic, catalog, without_semantics, {})
        self.assertEqual(
            [(edge["edge_id"], edge["status"]) for edge in with_semantics["edges"]],
            [(edge["edge_id"], edge["status"]) for edge in legacy["edges"]],
        )


if __name__ == "__main__":
    unittest.main()
