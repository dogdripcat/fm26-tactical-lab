import existing_evidence_package_candidates
import role_behaviours
import role_constraints
import role_evidence_snapshot


def test_identity_only_availability_evidence_is_not_promoted_to_behaviour():
    snapshot = role_evidence_snapshot.build_role_evidence_snapshot(
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base())
    report = existing_evidence_package_candidates.build_existing_evidence_package_candidates(snapshot)
    assert report["summary"]["identity_only_roles_reviewed"] == 57
    assert report["candidates"] == []
    assert report["summary"]["roles_with_actual_behaviour_evidence_candidates"] == 0
    assert report["summary"]["semantic_mapping_candidates"] == 0
    assert report["summary"]["ers_mapping_candidates"] == 0
    assert len(report["summary"]["existing_non_behaviour_evidence"]) == 9
