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
        self.assertEqual(3, len(set(payload["presets"]["3-4-3"]) & {"LCB", "CB", "RCB"}))

    def test_two_and_three_cb_presets_pass_the_actual_constraint_count(self):
        two_count = len(set(api.FORMATION_PRESETS["4-3-3"]) & {"LCB", "CB", "RCB"})
        three_count = len(set(api.FORMATION_PRESETS["3-5-2"]) & {"LCB", "CB", "RCB"})
        self.assertNotIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in api.roles_payload("IP", "LCB", two_count)["roles"]})
        self.assertIn("catalog:ip:centre-back:wcb", {row["role_internal_id"] for row in api.roles_payload("IP", "LCB", three_count)["roles"]})

    def test_unverified_abbreviation_is_not_exposed_as_a_verified_selector_token(self):
        payload = api.roles_payload("IP", "ST")
        self.assertTrue(all(row["abbreviation"]["verification"] != "user_ingame_verified" or row["abbreviation"]["value"]
                            for row in payload["roles"]))

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


if __name__ == "__main__": unittest.main()
