"""Read-only consistency audit for the derived role-evidence snapshot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import role_evidence_snapshot
import role_behaviours
import role_constraints


DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "role_evidence_snapshot.json"


def _ids(rows: List[Dict[str, Any]]) -> List[str]:
    return [row["role_internal_id"] for row in rows]


def build_role_evidence_snapshot_audit(snapshot: Dict[str, Any], catalog: List[Dict[str, Any]],
                                       knowledge: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare the snapshot with current source of truth; no data is changed."""
    canonical = role_evidence_snapshot.build_role_evidence_snapshot(catalog, knowledge)
    source_rows = {row["role_internal_id"]: row for row in canonical["roles"]}
    snapshot_rows = {row["role_internal_id"]: row for row in snapshot.get("roles", [])}
    fields = ("phase", "role_name_ko", "role_identity_status", "ambiguity", "abbreviation",
              "coverage_status", "evidence", "behaviours", "semantics", "expected_role_space",
              "formation_constraints")
    mismatches = []
    for role_id in sorted(set(source_rows) | set(snapshot_rows)):
        if role_id not in source_rows or role_id not in snapshot_rows:
            mismatches.append({"role_internal_id": role_id, "reason": "missing_role"})
            continue
        changed = [field for field in fields if snapshot_rows[role_id].get(field) != source_rows[role_id].get(field)]
        if changed:
            mismatches.append({"role_internal_id": role_id, "fields": changed})

    abbreviation_rows = [{
        "role_internal_id": row["role_internal_id"], "role_name_ko": row["role_name_ko"],
        "phase": row["phase"], "abbreviation": row["abbreviation"],
        "role_identity_status": row["role_identity_status"], "ambiguity": row["ambiguity"],
    } for row in canonical["roles"]]
    abbreviation_groups = {
        "verified": [row["role_internal_id"] for row in abbreviation_rows
                     if row["abbreviation"]["verification"] == "user_ingame_verified"],
        "unverified": [row["role_internal_id"] for row in abbreviation_rows
                       if row["abbreviation"]["verification"] != "user_ingame_verified"],
        "unresolved": [],
    }
    summary = canonical["summary"]
    user_ids = set(summary["roles_with_user_ingame_evidence"])
    official_ids = set(summary["roles_with_official_evidence"])
    evidence_ids = {row["role_internal_id"] for row in canonical["roles"] if row["evidence"]}
    coverage_sets = {key: summary[key] for key in (
        "roles_with_no_evidence", "identity_only_roles", "partial_roles", "unresolved_roles",
        "roles_with_semantics", "roles_without_semantics", "ers_supported_roles", "ers_unknown_roles",
        "roles_with_user_ingame_evidence", "roles_with_official_evidence", "multi_family_role_identities",
    )}
    return {
        "audit_type": "role_evidence_snapshot_consistency",
        "source_catalog_summary": canonical["catalog_summary"],
        "snapshot_catalog_summary": snapshot.get("catalog_summary"),
        "consistent": not mismatches and snapshot.get("catalog_summary") == canonical["catalog_summary"],
        "source_snapshot_mismatches": mismatches,
        "abbreviation_rows": abbreviation_rows,
        "abbreviation_groups": abbreviation_groups,
        "abbreviation_summary": {key: len(value) for key, value in abbreviation_groups.items()},
        "role_identity_unresolved": [row for row in abbreviation_rows if row["role_identity_status"] == "unresolved"],
        "coverage_sets": coverage_sets,
        "coverage_counts": {key: len(value) for key, value in coverage_sets.items()},
        "evidence_overlap": {
            "identities_with_any_evidence": sorted(evidence_ids),
            "user_ingame_and_official": sorted(user_ids & official_ids),
            "user_ingame_only": sorted(user_ids - official_ids),
            "official_only": sorted(official_ids - user_ids),
        },
        "baseline_comparison": {
            "declared_abbreviation_baseline": {"verified": 15, "unverified": 54},
            "current_catalog": {"verified": len(abbreviation_groups["verified"]), "unverified": len(abbreviation_groups["unverified"])},
            "matches_declared_baseline": len(abbreviation_groups["verified"]) == 15 and len(abbreviation_groups["unverified"]) == 54,
            "historical_file_change_determinable": False,
            "note": "A previous file hash/version was not supplied; this audit compares current source values to the declared count baseline only.",
        },
        "interpretation": [
            "Role identity ambiguity and display-abbreviation verification are independent fields.",
            "PW has a user_ingame_verified display abbreviation while its role identity ambiguity remains unresolved.",
            "OOP sweeper keeper has an unverified null display abbreviation; it is not a role-identity ambiguity record.",
        ],
    }


def load_and_audit(path: str | Path = DEFAULT_SNAPSHOT_PATH) -> Dict[str, Any]:
    snapshot = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return build_role_evidence_snapshot_audit(
        snapshot, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(),
    )
