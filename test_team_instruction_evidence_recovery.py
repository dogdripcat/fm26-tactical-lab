"""Evidence-only recovery guardrails for the Team Instruction catalogue."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class TeamInstructionEvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads((ROOT / "data" / "team_instruction_catalog.json").read_text(encoding="utf-8"))
        cls.static = json.loads((ROOT / "web" / "static" / "data" / "team_instruction_catalog.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "data" / "team_instruction_evidence.json").read_text(encoding="utf-8"))
        cls.evidence = {row["evidence_id"]: row for row in registry["evidence"]}

    def test_canonical_and_static_catalogues_remain_identical(self):
        self.assertEqual(self.canonical, self.static)

    def test_every_selectable_value_has_traceable_user_evidence_and_no_unset_sentinel(self):
        for category in self.canonical["instructions"]:
            for value in category["selectable_values"]:
                self.assertNotEqual("미설정", value["display_label_ko"])
                self.assertIn(value["provenance"], {"user_ingame_verified", "user_transcribed", "project_evidence"})
                self.assertTrue(value["source_reference"])
                self.assertEqual(value["source_reference"], value["evidence_ids"])
                self.assertTrue(set(value["source_reference"]).issubset(self.evidence))

    def test_recovery_audit_preserves_only_supported_complete_sets_and_partial_gaps(self):
        rows = self.canonical["instructions"]
        self.assertEqual(18, sum(row["phase"] == "IP" for row in rows))
        self.assertEqual(9, sum(row["phase"] == "OOP" for row in rows))
        self.assertEqual(5, sum(row["completion_status"] == "complete" for row in rows))
        self.assertEqual(22, sum(row["completion_status"] == "partial" for row in rows))
        self.assertEqual(
            {"passing_directness", "tempo", "attacking_width", "pressing_line", "set_piece_inducement"},
            {row["internal_id"] for row in rows if row["completion_status"] == "complete"},
        )


if __name__ == "__main__":
    unittest.main()
