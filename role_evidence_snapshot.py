"""Read-only export of the registered FM26 role-evidence state."""
from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import expected_role_space
import role_behaviours
import role_constraints
import role_knowledge_coverage


GROUPS = ("send", "receive", "space", "movement")
ERS_FIELDS = ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions")
VERIFIED = frozenset(("verified", "official", "user_ingame_verified"))


def _evidence_verification(item: Dict[str, Any]) -> str:
    """Use the existing registry's source-level view when no level was stored."""
    if item.get("evidence_level"):
        return item["evidence_level"]
    return {"user_ingame_capture": "user_ingame_verified", "official": "official_verified"}.get(
        item.get("source_type"), "unresolved"
    )


def _behaviour_entry(role: Dict[str, Any], knowledge: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    reference = role.get("role_behaviour_ref")
    return next((item for item in knowledge if reference and item["phase"] == reference["phase"]
                 and item["role"] == reference["role"]), None)


def _evidence(role: Dict[str, Any], entry: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Merge existing catalog/KB provenance, retaining its original labels and order."""
    output, seen = [], set()
    for item in list(role.get("evidence", [])) + list((entry or {}).get("evidence", [])):
        evidence_id = item.get("evidence_id")
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        output.append({
            "evidence_id": evidence_id,
            "source_kind": item.get("source_type"),
            "verification": _evidence_verification(item),
            "title": item.get("title"),
        })
    return output


def _behaviours(entry: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    if not entry or not entry.get("behaviour_verified"):
        return []
    output = []
    for behaviour in entry["behaviours"]:
        if behaviour.get("verification") not in VERIFIED or not behaviour.get("evidence_ids"):
            continue
        semantic_ids = []
        for items in behaviour.get("connectivity_semantics", {}).values():
            for semantic in items:
                if semantic.get("verification") in VERIFIED and semantic.get("evidence_ids"):
                    semantic_ids.append(semantic["semantic_id"])
        output.append({
            "behaviour_id": behaviour["behaviour_id"],
            "claim": behaviour["claim"],
            "verification": behaviour["verification"],
            "evidence_ids": copy.deepcopy(behaviour["evidence_ids"]),
            "semantic_ids": semantic_ids,
        })
    return output


def _semantics(entry: Dict[str, Any] | None) -> Dict[str, List[Dict[str, Any]]]:
    output = {group: [] for group in GROUPS}
    if not entry or not entry.get("behaviour_verified"):
        return output
    for behaviour in entry["behaviours"]:
        if behaviour.get("verification") not in VERIFIED or not behaviour.get("evidence_ids"):
            continue
        for group, items in behaviour.get("connectivity_semantics", {}).items():
            for semantic in items:
                if semantic.get("verification") not in VERIFIED or not semantic.get("evidence_ids"):
                    continue
                output[group].append({
                    "semantic_id": semantic["semantic_id"],
                    "behaviour_id": behaviour["behaviour_id"],
                    "evidence_ids": copy.deepcopy(semantic["evidence_ids"]),
                    "verification": semantic["verification"],
                    "edge_eligible": semantic.get("edge_eligible") is not False,
                })
    return output


def _abbreviation_summary(role: Dict[str, Any]) -> str:
    return "verified" if role["display_abbr_verification"] == "user_ingame_verified" else "unverified"


def build_role_evidence_snapshot(catalog: List[Dict[str, Any]] | None = None,
                                 knowledge: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Build a JSON-compatible snapshot without changing any catalog or KB input."""
    catalog = role_constraints.load_role_catalog() if catalog is None else role_constraints.validate_role_catalog(catalog)
    knowledge = role_behaviours.load_knowledge_base() if knowledge is None else role_behaviours.validate_knowledge_base(knowledge)
    coverage = role_knowledge_coverage.build_coverage_report(catalog, knowledge)
    status_by_id = {item["internal_id"]: item["status"] for item in coverage["roles"]}
    rows = []
    for role in catalog:
        entry = _behaviour_entry(role, knowledge)
        ers = expected_role_space.build_expected_role_space(role["internal_id"], role["phase"], catalog, knowledge)["expected_role_space"]
        rows.append({
            "role_internal_id": role["internal_id"],
            "phase": role["phase"],
            "role_name_ko": role["role_name_ko"],
            "role_identity_status": "unresolved" if role.get("ambiguity", {}).get("status") == "unresolved" else "resolved",
            "ambiguity": copy.deepcopy(role.get("ambiguity", {"status": "none"})),
            "role_families": copy.deepcopy(role["role_families"]),
            "available_starting_positions": copy.deepcopy(role["available_starting_positions"]),
            "abbreviation": {"value": role["display_abbr"], "verification": role["display_abbr_verification"]},
            "coverage_status": status_by_id[role["internal_id"]],
            "evidence": _evidence(role, entry),
            "behaviours": _behaviours(entry),
            "semantics": _semantics(entry),
            "expected_role_space": {
                "status": ers["status"],
                **{field: copy.deepcopy(ers[field]) for field in ERS_FIELDS},
            },
            "formation_constraints": copy.deepcopy(role["formation_constraints"]),
            "limitations": copy.deepcopy(ers["limitations"]),
        })
    summary = {
        "roles_with_no_evidence": [row["role_internal_id"] for row in rows if not row["evidence"]],
        "identity_only_roles": [row["role_internal_id"] for row in rows if row["coverage_status"] == "identity_only"],
        "partial_roles": [row["role_internal_id"] for row in rows if row["coverage_status"] == "partial"],
        "unresolved_roles": [row["role_internal_id"] for row in rows if row["coverage_status"] == "unresolved"],
        "roles_with_semantics": [row["role_internal_id"] for row in rows if any(row["semantics"].values())],
        "roles_without_semantics": [row["role_internal_id"] for row in rows if not any(row["semantics"].values())],
        "ers_supported_roles": [row["role_internal_id"] for row in rows if row["expected_role_space"]["status"] == "supported"],
        "ers_unknown_roles": [row["role_internal_id"] for row in rows if row["expected_role_space"]["status"] == "unknown"],
        "roles_with_user_ingame_evidence": [row["role_internal_id"] for row in rows if any(item["source_kind"] == "user_ingame_capture" for item in row["evidence"])],
        "roles_with_official_evidence": [row["role_internal_id"] for row in rows if any(item["source_kind"] == "official" for item in row["evidence"])],
        "multi_family_role_identities": [row["role_internal_id"] for row in rows if len(row["role_families"]) > 1],
        "abbreviation_status": {
            "verified": sum(_abbreviation_summary(role) == "verified" for role in catalog),
            "unverified": sum(_abbreviation_summary(role) == "unverified" for role in catalog),
            "unresolved": 0,
        },
    }
    return {
        "snapshot_type": "role_evidence_database",
        "catalog_summary": {
            "total": len(rows),
            "ip": sum(row["phase"] == "IP" for row in rows),
            "oop": sum(row["phase"] == "OOP" for row in rows),
        },
        "roles": rows,
        "summary": summary,
        "limitations": [
            "This is a read-only export of registered evidence and mappings; it creates no inference.",
            "IP and OOP identities remain distinct; shared configured positions do not duplicate identities.",
        ],
    }


def write_role_evidence_snapshot(path: str | Path, catalog: List[Dict[str, Any]] | None = None,
                                 knowledge: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Write only the requested derived snapshot file."""
    snapshot = build_role_evidence_snapshot(catalog, knowledge)
    Path(path).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snapshot
