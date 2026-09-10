import copy
import unittest

from web import api


class WebApiTests(unittest.TestCase):
    def test_health_contract_is_static(self):
        self.assertEqual({"status": "ok"}, {"status": "ok"})

    def test_roles_are_catalog_backed_and_phase_filtered(self):
        payload = api.roles_payload("IP", "ST")
        self.assertTrue(payload["roles"])
        self.assertTrue(all(row["phase"] == "IP" for row in payload["roles"]))
        self.assertTrue(all("FW" in row["available_starting_positions"] for row in payload["roles"]))

    def test_three_cb_constraint_uses_existing_availability(self):
        two = api.roles_payload("IP", "LCB", 2)
        three = api.roles_payload("IP", "LCB", 3)
        self.assertNotIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in two["roles"]})
        self.assertIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in three["roles"]})
        self.assertIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in two["unavailable_roles"]})

    def test_presets_are_configured_position_templates_only(self):
        payload = api.formation_presets_payload()
        self.assertEqual("IP", payload["phase"])
        self.assertEqual(7, len(payload["presets"]))
        self.assertTrue(all(len(positions) == 11 and len(set(positions)) == 11
                            for positions in payload["presets"].values()))
        self.assertEqual(3, api.centre_back_line_count(payload["presets"]["3-4-3"]))
        for preset in ("3-4-2-1", "3-4-3", "3-5-2"):
            self.assertIn("wing_back_left", payload["presets"][preset])
            self.assertIn("wing_back_right", payload["presets"][preset])
            self.assertNotIn("ML", payload["presets"][preset])
            self.assertNotIn("MR", payload["presets"][preset])

    def test_two_and_three_cb_presets_pass_the_actual_constraint_count(self):
        two_count = api.centre_back_line_count(api.FORMATION_PRESETS["4-3-3"])
        three_count = api.centre_back_line_count(api.FORMATION_PRESETS["3-5-2"])
        self.assertNotIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in api.roles_payload("IP", "LCB", two_count)["roles"]})
        self.assertIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in api.roles_payload("IP", "LCB", three_count)["roles"]})

    def test_unverified_abbreviation_is_not_exposed_as_a_verified_selector_token(self):
        payload = api.roles_payload("IP", "ST")
        self.assertTrue(all(row["abbreviation"]["verification"] != "user_ingame_verified" or row["abbreviation"]["value"]
                            for row in payload["roles"]))

    def test_wing_back_wide_midfield_and_full_back_selectors_remain_distinct(self):
        wing_back = {row["role_internal_id"] for row in api.roles_payload("IP", "wing_back_left")["roles"]}
        wide_midfield = {row["role_internal_id"] for row in api.roles_payload("IP", "ML")["roles"]}
        full_back = {row["role_internal_id"] for row in api.roles_payload("IP", "LB")["roles"]}
        self.assertIn("catalog:ip:wing-back:wb", wing_back)
        self.assertNotIn("catalog:ip:wing-back:wb", wide_midfield)
        self.assertIn("catalog:ip:wing-back:wb", full_back)  # verified Full-Back availability is preserved

    def test_new_wing_back_positions_do_not_invent_game_abbreviations(self):
        registry = api.json.loads(api.POSITION_REGISTRY_PATH.read_text(encoding="utf-8-sig"))
        rows = {item["position_id"]: item for item in registry["positions"]}
        for position in ("wing_back_left", "wing_back_right"):
            self.assertIsNone(rows[position]["game_abbreviation"])
            self.assertEqual("unverified", rows[position]["abbreviation_verification"])

    def test_evidence_sufficiency_adapter_is_read_only(self):
        source = api.sample_tactic(); before = copy.deepcopy(source)
        report = api.evidence_sufficiency_payload(source)
        self.assertEqual(source, before)
        self.assertEqual("current_tactic_evidence_sufficiency", report["report_type"])

    def test_public_role_contract_has_no_invented_abbreviation(self):
        for row in api.roles_payload("IP", "ST")["roles"]:
            self.assertIn("analysis_token", row)
            self.assertIn("accepted_input_tokens", row)
            if row["abbreviation"]["verification"] != "user_ingame_verified":
                self.assertEqual(row["role_internal_id"], row["analysis_token"])

    def test_analyze_calls_core_and_preserves_connectivity_provenance(self):
        source = api.sample_tactic(); before = copy.deepcopy(source)
        result = api.analyze_payload(source)
        self.assertEqual(source, before)
        self.assertIn("connectivity", result)
        self.assertTrue(result["connectivity"]["edges"])
        self.assertIn("provenance", result["connectivity"]["edges"][0])

    def test_invalid_tactic_is_rejected(self):
        with self.assertRaises(ValueError):
            api.analyze_payload([])

    def test_team_instruction_catalogue_and_web_fixture_are_available(self):
        payload = api.team_instructions_payload()
        self.assertEqual(18, len(payload["IP"]))
        self.assertEqual(9, len(payload["OOP"]))
        self.assertEqual({}, api.team_instructions_payload("IP").get("OOP", {}))
        self.assertIn("ip_team_instructions", api.sample_team_instructions_payload())

    def test_invalid_role_position_selection_is_rejected_before_analysis(self):
        tactic = api.sample_tactic()
        tactic["ip_formation"] = "4-2-3-1"
        tactic["ip_roles"] = {position: None for position in api.FORMATION_PRESETS["4-2-3-1"]}
        tactic["ip_roles"].update({"GK": "BPGK", "LB": "WB", "LCB": "CB", "RCB": "CB", "RB": "IWB", "DML": "DLP", "DMR": "BBP", "AML": "IF", "AMC": "AM", "AMR": "WF", "ST": "IWB"})
        with self.assertRaises(ValueError):
            api.analyze_payload(tactic)

    def test_analyze_response_adds_phase_aware_input_without_breaking_connectivity(self):
        tactic = api.sample_tactic()
        tactic.update(api.sample_team_instructions_payload())
        result = api.analyze_payload(tactic)
        self.assertIn("connectivity", result)
        self.assertEqual("limited", result["tactic_input"]["out_of_possession"]["editing_status"])
        self.assertEqual(tactic["ip_team_instructions"], result["tactic_input"]["in_possession"]["team_instructions"])

    def test_pitch_layout_is_display_only_and_covers_every_preset(self):
        payload = api.pitch_layout_payload_for_presets()
        self.assertTrue(payload["display_only"])
        self.assertEqual(set(api.FORMATION_PRESETS), set(payload["coordinates"]))


if __name__ == "__main__": unittest.main()
