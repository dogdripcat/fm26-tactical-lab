import unittest
from collections import Counter

import role_behaviours
import role_constraints


class RoleCatalogExpansionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = role_constraints.load_role_catalog()
        self.resolved = role_constraints.resolve_catalog(
            self.catalog, role_behaviours.load_knowledge_base()
        )

    def test_user_confirmed_role_counts_are_registered_by_phase(self):
        self.assertEqual(len(self.catalog), 69)
        self.assertEqual(Counter(role["phase"] for role in self.catalog), {"IP": 37, "OOP": 32})

    def test_role_family_memberships_preserve_shared_starting_positions(self):
        counts = Counter(
            (role["phase"], family)
            for role in self.catalog
            for family in role["role_families"]
        )
        self.assertEqual(counts[("IP", "Winger")], 6)
        self.assertEqual(counts[("IP", "CM")], 6)
        self.assertEqual(counts[("IP", "Full-Back")], 5)
        self.assertEqual(counts[("OOP", "Centre-Back")], 6)
        self.assertEqual(counts[("OOP", "FW")], 0)

    def test_existing_behaviour_references_are_kept_and_new_roles_remain_unknown(self):
        behaviours_by_role = {
            role["internal_id"]: role["described_behaviours"]
            for role in self.resolved
        }
        self.assertTrue(behaviours_by_role["catalog:ip:winger:if"])
        self.assertTrue(behaviours_by_role["catalog:ip:winger:wfd"])
        self.assertEqual(behaviours_by_role["catalog:ip:winger:inside-winger"], [])
        self.assertEqual(behaviours_by_role["catalog:oop:winger:tracking-winger"], [])

    def test_unverified_abbreviations_are_not_invented(self):
        statuses = Counter(role["display_abbr_verification"] for role in self.catalog)
        self.assertEqual(statuses, {"user_ingame_verified": 15, "unverified": 54})
        for role in self.catalog:
            if role["display_abbr_verification"] == "unverified":
                self.assertIsNone(role["display_abbr"])

    def test_ambiguous_playmaking_winger_names_remain_distinct(self):
        first = next(role for role in self.catalog if role["internal_id"] == "catalog:ip:winger:pw-legacy-name")
        second = next(role for role in self.catalog if role["internal_id"] == "catalog:ip:winger:playmaking-winger")
        self.assertNotEqual(first["internal_id"], second["internal_id"])
        self.assertEqual(first["ambiguity"]["status"], "unresolved")
        self.assertEqual(second["ambiguity"]["status"], "unresolved")

    def test_three_centre_back_constraints_remain_exact_equality(self):
        constrained = [
            role for role in self.catalog
            if role["formation_constraints"]
        ]
        self.assertEqual(len(constrained), 6)
        for role in constrained:
            constraint = role["formation_constraints"][0]
            self.assertEqual(constraint["comparison"], "eq")
            self.assertEqual(constraint["value"], 3)


if __name__ == "__main__":
    unittest.main()
