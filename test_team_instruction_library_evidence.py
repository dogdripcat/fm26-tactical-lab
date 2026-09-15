"""Guardrails for terminology-only Team Instruction recovery candidates."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class TeamInstructionLibraryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "data" / "team_instruction_catalog.json").read_text(encoding="utf-8"))
        cls.static_catalog = json.loads((ROOT / "web" / "static" / "data" / "team_instruction_catalog.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "data" / "team_instruction_evidence.json").read_text(encoding="utf-8"))
        cls.static_registry = json.loads((ROOT / "web" / "static" / "data" / "team_instruction_evidence.json").read_text(encoding="utf-8"))
        cls.candidates = json.loads((ROOT / "data" / "team_instruction_library_candidates.json").read_text(encoding="utf-8"))

    def test_library_terminology_has_a_traceable_non_selectable_evidence_record(self):
        record = next(row for row in self.registry["evidence"] if row["evidence_id"] == "CHATGPT_LIBRARY_FM26_TERMS_001")
        self.assertEqual("terminology_supported", record["verification"])
        self.assertEqual(self.registry, self.static_registry)

    def test_terminology_only_candidates_never_become_selectable_values(self):
        selectable = {value["display_label_ko"] for category in self.catalog["instructions"] for value in category["selectable_values"]}
        for candidate in self.candidates["candidates"]:
            with self.subTest(candidate=candidate["term_ko"]):
                self.assertIn(candidate["status"], {"already_verified", "terminology_supported", "selectable_terminology_supported", "unresolved"})
                if candidate["status"] in {"terminology_supported", "unresolved"}:
                    self.assertNotIn(candidate["term_ko"], selectable)

    def test_direct_ui_labels_and_catalogue_parity_remain_authoritative(self):
        self.assertEqual(self.catalog, self.static_catalog)
        by_id = {row["internal_id"]: row for row in self.catalog["instructions"]}
        self.assertEqual("강한 압박", by_id["pressing_line"]["selectable_values"][2]["display_label_ko"])
        self.assertEqual("더 높은 위치로", by_id["defensive_line_action"]["selectable_values"][0]["display_label_ko"])
        self.assertEqual("강하게 태클하라", by_id["tackling"]["selectable_values"][0]["display_label_ko"])


if __name__ == "__main__":
    unittest.main()
