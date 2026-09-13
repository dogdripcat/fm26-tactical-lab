"""Tests for evidence-backed role key attributes, not player recommendation scoring."""
from __future__ import annotations

import copy
from pathlib import Path
import unittest

import role_attribute_profiles as profiles
from web import api


ROOT = Path(__file__).resolve().parent
CFD = "catalog:ip:fw:cfd"


class RoleAttributeProfileTests(unittest.TestCase):
    def test_centre_forward_profile_exactly_matches_user_supplied_attribute_names(self):
        profile = profiles.profile_for_role(CFD, "IP")
        self.assertIsNotNone(profile)
        self.assertEqual(
            [item["attribute_id"] for item in profile["key_attributes"]],
            ["finishing", "heading", "off_the_ball", "first_touch", "flair", "acceleration", "strength", "composure"],
        )
        self.assertEqual(
            [item["name_ko"] for item in profile["key_attributes"]],
            ["골 결정력", "헤더", "오프 더 볼", "퍼스트 터치", "개인기", "가속도", "몸싸움", "침착성"],
        )
        self.assertTrue(all(item["verification"] == "user_ingame_verified" for item in profile["key_attributes"]))

    def test_profiles_store_no_player_values_or_role_thresholds(self):
        registry = profiles.load_role_attribute_profiles()
        encoded = str(registry).lower()
        for field in ("threshold", "minimum", "recommended_value"):
            self.assertNotIn(field, encoded)
        self.assertNotIn("15", encoded)
        bad = copy.deepcopy(registry)
        bad["profiles"][0]["key_attributes"][0]["threshold"] = 15
        with self.assertRaises(ValueError):
            profiles.validate_role_attribute_profiles(bad, api.role_constraints.load_role_catalog())

    def test_profile_retrieval_requires_exact_role_identity_and_phase(self):
        self.assertIsNotNone(profiles.profile_for_role(CFD, "IP"))
        self.assertIsNone(profiles.profile_for_role(CFD, "OOP"))
        self.assertIsNone(profiles.profile_for_role("catalog:ip:fw:chf", "IP"))
        payload = api.role_attribute_profiles_payload(CFD, "IP")
        self.assertEqual([CFD], [item["role_internal_id"] for item in payload["profiles"]])

    def test_unresolved_roles_receive_no_guessed_profile(self):
        self.assertEqual([], api.role_attribute_profiles_payload("catalog:ip:winger:pw-legacy-name", "IP")["profiles"])
        self.assertEqual([], api.role_attribute_profiles_payload("catalog:oop:goalkeeper:sweeper-keeper", "OOP")["profiles"])

    def test_player_display_never_invents_values_or_recommendation(self):
        profile = profiles.profile_for_role(CFD, "IP")
        empty = profiles.player_attribute_display(profile)
        self.assertFalse(empty["player_data_available"])
        self.assertTrue(all(item["player_value"] is None for item in empty["attributes"]))
        self.assertIsNone(empty["fit_score"])
        self.assertIsNone(empty["recommendation"])
        supplied = profiles.player_attribute_display(profile, {"finishing": 15})
        self.assertEqual(15, supplied["attributes"][0]["player_value"])
        self.assertTrue(all(item["player_value"] is None for item in supplied["attributes"][1:]))

    def test_static_data_and_ui_keep_profile_display_separate_from_evaluators(self):
        static = ROOT / "web" / "static"
        self.assertTrue((static / "data" / "role_attribute_profiles.json").is_file())
        source = (static / "app.js").read_text(encoding="utf-8")
        self.assertIn("renderRoleAttributeProfile", source)
        self.assertIn("선수 수치나 역할 기준값을 뜻하지 않습니다.", source)
        self.assertNotIn("attributeProfiles", (static / "js" / "tactic_analysis.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
