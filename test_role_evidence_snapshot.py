import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import role_behaviours
import role_constraints
import role_evidence_snapshot


class RoleEvidenceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.catalog = role_constraints.load_role_catalog()
        self.knowledge = role_behaviours.load_knowledge_base()

    def test_snapshot_preserves_catalog_counts_and_coverage(self):
        report = role_evidence_snapshot.build_role_evidence_snapshot(self.catalog, self.knowledge)
        self.assertEqual(report["catalog_summary"], {"total": 69, "ip": 37, "oop": 32})
        self.assertEqual(len(report["summary"]["partial_roles"]), 10)
        self.assertEqual(len(report["summary"]["identity_only_roles"]), 57)
        self.assertEqual(len(report["summary"]["unresolved_roles"]), 2)
        self.assertEqual(len(report["summary"]["ers_supported_roles"]), 7)
        self.assertEqual(len(report["summary"]["ers_unknown_roles"]), 62)

    def test_snapshot_keeps_cfd_provenance_and_shared_am_identity(self):
        report = role_evidence_snapshot.build_role_evidence_snapshot(self.catalog, self.knowledge)
        by_id = {row["role_internal_id"]: row for row in report["roles"]}
        cfd = by_id["catalog:ip:fw:cfd"]
        self.assertIn("SI_FM26_DUAL_STRIKERS_2025", {item["evidence_id"] for item in cfd["evidence"]})
        self.assertIn("CFD_IP_ATTACKING_FOCAL_POINT", {item["behaviour_id"] for item in cfd["behaviours"]})
        self.assertEqual(by_id["catalog:ip:am:am"]["available_starting_positions"], ["AM", "CM"])

    def test_snapshot_does_not_change_source_inputs_and_writes_only_target(self):
        catalog_path = role_constraints.DEFAULT_PATH
        kb_path = role_behaviours.DEFAULT_PATH
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in (catalog_path, kb_path)]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "snapshot.json"
            role_evidence_snapshot.write_role_evidence_snapshot(target, self.catalog, self.knowledge)
            self.assertTrue(target.exists())
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["catalog_summary"]["total"], 69)
        after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in (catalog_path, kb_path)]
        self.assertEqual(before, after)

