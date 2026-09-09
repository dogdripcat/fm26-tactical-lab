import role_behaviours
import role_constraints
import role_evidence_snapshot
import role_evidence_snapshot_audit


def test_abbreviation_audit_does_not_conflate_identity_ambiguity():
    snapshot = role_evidence_snapshot.build_role_evidence_snapshot(
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
    audit = role_evidence_snapshot_audit.build_role_evidence_snapshot_audit(
        snapshot, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
    assert audit["consistent"] is True
    assert audit["abbreviation_summary"] == {"verified": 15, "unverified": 54, "unresolved": 0}
    pw = next(row for row in audit["abbreviation_rows"] if row["role_internal_id"] == "catalog:ip:winger:pw-legacy-name")
    assert pw["role_identity_status"] == "unresolved"
    assert pw["abbreviation"]["verification"] == "user_ingame_verified"


def test_snapshot_audit_preserves_coverage_sets_and_evidence_overlap():
    snapshot = role_evidence_snapshot.build_role_evidence_snapshot(
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
    audit = role_evidence_snapshot_audit.build_role_evidence_snapshot_audit(
        snapshot, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
    assert audit["coverage_counts"]["partial_roles"] == 10
    assert audit["coverage_counts"]["ers_supported_roles"] == 7
    assert audit["evidence_overlap"]["user_ingame_and_official"] == ["catalog:ip:fw:cfd"]
