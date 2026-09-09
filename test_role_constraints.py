import unittest

import role_constraints as constraints
import role_behaviours


class RoleConstraintTests(unittest.TestCase):
    def setUp(self):
        self.catalog = constraints.load_role_catalog()

    def role(self, internal_id):
        return next(row for row in self.catalog if row["internal_id"] == internal_id)

    def test_oop_wide_centre_backs_require_three(self):
        targets = (
            "catalog:oop:centre-back:wide-centre-back",
            "catalog:oop:centre-back:stopping-wide-centre-back",
            "catalog:oop:centre-back:covering-wide-centre-back",
        )
        for internal_id in targets:
            with self.subTest(internal_id=internal_id):
                role = self.role(internal_id)
                self.assertEqual(constraints.role_availability(role, 2)["status"], "inactive")
                self.assertEqual(constraints.role_availability(role, 3)["status"], "active")
                self.assertEqual(constraints.role_availability(role, 4)["status"], "inactive")

    def test_oop_standard_centre_backs_have_no_three_only_constraint(self):
        targets = (
            "catalog:oop:centre-back:centre-back",
            "catalog:oop:centre-back:stopping-centre-back",
            "catalog:oop:centre-back:covering-centre-back",
        )
        for internal_id in targets:
            with self.subTest(internal_id=internal_id):
                role = self.role(internal_id)
                self.assertEqual(role["formation_constraints"], [])
                self.assertEqual(constraints.role_availability(role, 2)["status"], "no_verified_restriction")

    def test_ip_and_oop_constraints_are_separate(self):
        ip = self.role("catalog:ip:centre-back:wcb")
        oop = self.role("catalog:oop:centre-back:wide-centre-back")
        self.assertNotEqual(ip["internal_id"], oop["internal_id"])
        self.assertEqual(ip["phase"], "IP")
        self.assertEqual(oop["phase"], "OOP")
        self.assertIsNone(ip["role_behaviour_ref"])
        self.assertIsNone(oop["role_behaviour_ref"])

    def test_same_display_abbreviation_is_not_identity(self):
        identifiers = [role["internal_id"] for role in self.catalog]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(constraints.role_availability(self.role("catalog:oop:centre-back:wide-centre-back"), None)["status"], "unknown")

    def test_existing_behaviour_data_is_referenced_not_duplicated(self):
        resolved = constraints.resolve_catalog(self.catalog, role_behaviours.load_knowledge_base())
        wfd = next(row for row in resolved if row["internal_id"] == "catalog:ip:winger:wfd")
        self.assertEqual(len(wfd["role_tags"]), 1)
        self.assertEqual(len(wfd["described_behaviours"]), 5)
        self.assertEqual(wfd["player_instructions"], [])
        self.assertTrue(wfd["evidence"])
        original = self.role("catalog:ip:winger:wfd")
        self.assertNotIn("described_behaviours", original)


if __name__ == "__main__":
    unittest.main()
