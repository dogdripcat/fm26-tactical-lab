"""Read-only discovery of importable behaviour claims already present in source data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "role_evidence_snapshot.json"


def build_existing_evidence_package_candidates(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Find only explicit, unimported behaviour claims; never derive claims from names or constraints."""
    roles = snapshot.get("roles", [])
    partial = [row["role_internal_id"] for row in roles if row.get("coverage_status") == "partial"]
    unresolved = [row["role_internal_id"] for row in roles if row.get("coverage_status") == "unresolved"]
    identity_only = [row for row in roles if row.get("coverage_status") == "identity_only"]
    non_behaviour_evidence = []
    for role in identity_only:
        if not role.get("evidence"):
            continue
        # The source snapshot contains no registered behaviour claim for these identities.
        # Constraints are UI availability evidence and intentionally cannot become behaviour candidates.
        non_behaviour_evidence.append({
            "role_internal_id": role["role_internal_id"],
            "phase": role["phase"],
            "role_name_ko": role["role_name_ko"],
            "existing_evidence_ids": [item["evidence_id"] for item in role["evidence"]],
            "reason_excluded": "existing evidence records UI availability/formation constraints only; no explicit behaviour claim is registered.",
        })
    return {
        "report_type": "existing_user_evidence_role_package_candidates",
        "candidates": [],
        "summary": {
            "identity_only_roles_reviewed": len(identity_only),
            "roles_with_actual_behaviour_evidence_candidates": 0,
            "ready_for_import_roles": [],
            "evidence_insufficient_roles": [role["role_internal_id"] for role in identity_only],
            "semantic_mapping_candidates": 0,
            "ers_mapping_candidates": 0,
            "unresolved_excluded_roles": unresolved,
            "partial_excluded_roles": partial,
            "existing_non_behaviour_evidence": non_behaviour_evidence,
        },
        "limitations": [
            "No identity_only role has a registered explicit behaviour claim in the current snapshot.",
            "UI availability/formation constraints are not role behaviours and are excluded from import candidates.",
            "No semantic or ERS mapping is proposed without an explicit imported claim.",
        ],
    }


def load_existing_evidence_package_candidates(path: str | Path = DEFAULT_SNAPSHOT_PATH) -> Dict[str, Any]:
    return build_existing_evidence_package_candidates(json.loads(Path(path).read_text(encoding="utf-8-sig")))
