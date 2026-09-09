import copy
import json
from pathlib import Path
import tempfile
import unittest

import role_behaviours
import role_constraints
import role_evidence_importer as importer


def package(role_id="catalog:ip:centre-back:cb", phase="IP", role_name="중앙 수비수", evidence_id="TEST_USER_CB_DESCRIPTION_001"):
    return {
        "role_internal_id": role_id,
        "phase": phase,
        "role_name_ko": role_name,
        "source_kind": "user_ingame",
        "evidence_id": evidence_id,
        "evidence": {
            "evidence_id": evidence_id, "source_type": "user_ingame_capture",
            "title": "Synthetic importer test", "source": "test:role-evidence-importer",
            "accessed": "2026-09-08", "notes": "Schema fixture only; not a football claim.",
        },
        "role_description": "Synthetic reviewed text.",
        "role_tags": ["Synthetic tag"],
        "player_instructions": [],
        "key_attributes": ["Synthetic attribute"],
        "formation_constraints": [],
        "behaviours": [{
            "behaviour_id": "TEST_CB_REVIEWED_TEXT", "claim": "Synthetic reviewed claim.",
            "semantic_mappings": [{"semantic_id": "send_forward"}],
        }],
    }


class RoleEvidenceImporterTests(unittest.TestCase):
    def setUp(self):
        self.catalog = role_constraints.load_role_catalog()
        self.kb = role_behaviours.load_knowledge_base()

    def test_valid_package_is_dry_run_and_reports_coverage_change(self):
        before_catalog = copy.deepcopy(self.catalog)
        before_kb = copy.deepcopy(self.kb)
        result = importer.validate_role_evidence(package(), self.catalog, self.kb)
        self.assertTrue(result["valid"])
        self.assertEqual(self.catalog, before_catalog)
        self.assertEqual(self.kb, before_kb)
        changes = result["proposed_changes"]
        self.assertEqual(changes["roles_changed"], ["catalog:ip:centre-back:cb"])
        self.assertEqual(changes["behaviours_added"], 1)
        self.assertEqual(changes["semantic_mappings_added"], 1)
        self.assertEqual(changes["evidence_added"], 1)
        self.assertEqual(changes["coverage_before"]["partial"], 10)
        self.assertEqual(changes["coverage_after"]["partial"], 10)

    def test_unknown_role_and_phase_mismatch_are_rejected(self):
        unknown = importer.validate_role_evidence(package(role_id="catalog:ip:missing"), self.catalog, self.kb)
        self.assertFalse(unknown["valid"])
        mismatch = importer.validate_role_evidence(package(phase="OOP"), self.catalog, self.kb)
        self.assertFalse(mismatch["valid"])

    def test_duplicate_evidence_and_behaviour_conflict_are_rejected(self):
        duplicate = importer.validate_role_evidence(package(evidence_id="USER_FM26_DLP_DESCRIPTION"), self.catalog, self.kb)
        self.assertFalse(duplicate["valid"])
        conflict = package(role_id="catalog:ip:dm:dlp", role_name="딥라잉 플레이메이커")
        conflict["behaviours"][0]["behaviour_id"] = "DLP_IP_FORWARD_PASSES"
        conflict["behaviours"][0]["claim"] = "Different text must not overwrite existing behaviour."
        result = importer.validate_role_evidence(conflict, self.catalog, self.kb)
        self.assertFalse(result["valid"])
        self.assertIn("behaviour_id conflict", result["errors"])

    def test_unknown_semantic_and_invalid_constraint_are_rejected(self):
        bad_semantic = package()
        bad_semantic["behaviours"][0]["semantic_mappings"] = [{"semantic_id": "invented_semantic"}]
        self.assertFalse(importer.validate_role_evidence(bad_semantic, self.catalog, self.kb)["valid"])
        bad_constraint = package()
        bad_constraint["formation_constraints"] = [{"constraint_type": "unknown"}]
        self.assertFalse(importer.validate_role_evidence(bad_constraint, self.catalog, self.kb)["valid"])

    def test_abbreviation_edits_are_rejected(self):
        data = package()
        data["display_abbr"] = "MADE_UP"
        result = importer.validate_role_evidence(data, self.catalog, self.kb)
        self.assertFalse(result["valid"])

    def test_successful_apply_writes_only_the_staged_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "role_catalog.json"
            behaviour_path = Path(tmp) / "role_behaviours.json"
            catalog_path.write_text(json.dumps(self.catalog, ensure_ascii=False), encoding="utf-8")
            behaviour_path.write_text(json.dumps(self.kb, ensure_ascii=False), encoding="utf-8")
            result = importer.apply_role_evidence(package(), catalog_path, behaviour_path)
            self.assertTrue(result["valid"])
            applied_catalog = role_constraints.load_role_catalog(catalog_path)
            applied_kb = role_behaviours.load_knowledge_base(behaviour_path)
            self.assertEqual(result["proposed_changes"]["coverage_after"]["partial"], 10)
            self.assertEqual(len(applied_catalog), 69)
            self.assertTrue(any(row["behaviour_id"] == "TEST_CB_REVIEWED_TEXT" for row in next(row for row in applied_kb if row["role"] == "CB")["behaviours"]))

    def test_official_package_stages_existing_semantic_provenance_without_new_semantic(self):
        path = Path(__file__).resolve().parent / "data" / "official_evidence_packages" / "wfd_official_package.json"
        official = json.loads(path.read_text(encoding="utf-8"))
        result = importer.validate_role_evidence(official, self.catalog, self.kb)
        self.assertTrue(result["valid"])
        self.assertEqual(result["proposed_changes"]["semantic_mappings_added"], 0)
        staged = next(row for row in result["_behaviour_kb"] if row["role"] == "WFD")
        width = next(row for row in staged["behaviours"] if row["behaviour_id"] == "WFD_IP_MAINTAIN_WIDTH")
        semantic = width["connectivity_semantics"]["space"][0]
        self.assertIn("SI_FM26_WIDE_FORWARD_EN_2026", semantic["evidence_ids"])


if __name__ == "__main__":
    unittest.main()
