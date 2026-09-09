"""Read-only manifest for collecting only analysis evidence that is still absent.

It reports existing evidence before suggesting a new UI surface. It creates no
behaviour, semantic, ERS item, or compatibility rule.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

import expected_role_space
import role_behaviours
import role_constraints
import role_evidence_planning


VERIFIED = frozenset(("verified", "official", "user_ingame_verified"))
_FIELDS = ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions")
_DO_NOT_REINFER = {
    "send_simple_pass": "send_simple_pass != send_forward",
    "move_to_receive": "move_to_receive != receive",
    "receive_between_lines": "receive_between_lines != occupancy.between_lines",
    "receive_centrally": "receive_centrally != occupancy.central",
    "move_into_halfspace": "move_into_halfspace != occupancy.halfspace",
    "move_inside": "move_inside != occupancy.central 또는 movement_targets.central",
    "open_space_for_fullback": "open_space_for_fullback != 해당 역할의 중앙 이동",
    "support_central_passing_links": "support_central_passing_links != direct send 또는 direct receive",
}
_BEHAVIOUR_DO_NOT_REINFER = {
    "BGK_IP_ACTIVE_BUILDUP_PARTICIPATION": "active buildup participation != specific distribution target",
    "CFD_IP_ATTACKING_FOCAL_POINT": "attacking focal point != receive_centrally",
    "CFD_IP_CREATE_SCORING_OPPORTUNITIES": "chance creation != send semantic",
}


def _records_by_role(knowledge: List[Dict[str, Any]], catalog: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    output: Dict[str, List[Dict[str, Any]]] = {}
    for record in role_behaviours.behaviour_records(knowledge, catalog):
        if record["role_internal_id"] and record["verification"] in VERIFIED and record["evidence_ids"]:
            output.setdefault(record["role_internal_id"], []).append(record)
    return output


def _semantic_items(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []
    for record in records:
        for group, items in record["connectivity_semantics"].items():
            for item in items:
                if item.get("verification") in VERIFIED and item.get("evidence_ids"):
                    output.append({
                        "semantic_id": item["semantic_id"], "group": group,
                        "edge_eligible": item.get("edge_eligible") is not False,
                        "behaviour_ids": [record["behaviour_id"]],
                        "evidence_ids": copy.deepcopy(item["evidence_ids"]),
                    })
    return output


def _gap_fields(plan_role: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Separate analysis uncertainty from absent claims without expecting either claim to exist."""
    exposure = plan_role["source_target_edge_exposure"]
    semantics = plan_role["edge_eligible_semantics"]
    analysis_gaps, claim_missing = [], []
    if exposure["source"]["evidence_missing"] and not semantics["send"]:
        analysis_gaps.append("edge-eligible source distribution evidence unavailable")
        claim_missing.append("current evidence does not explicitly establish edge-eligible forward/progressive distribution")
    if exposure["target"]["evidence_missing"] and not semantics["receive"]:
        analysis_gaps.append("target reception evidence unavailable")
        claim_missing.append("current evidence does not explicitly establish receiving behaviour")
    if plan_role["ers_status"] == "unknown":
        analysis_gaps.append("Expected Role Space mapping unavailable")
        claim_missing.append("current evidence does not explicitly establish an Expected Role Space ontology-mapped concept")
    return analysis_gaps, claim_missing


def build_evidence_request_manifest(tactic: Dict[str, Any], catalog: List[Dict[str, Any]],
                                    knowledge: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str]) -> Dict[str, Any]:
    """Return evidence requests for already-evidenced Leicester roles without re-requesting their evidence."""
    catalog = role_constraints.validate_role_catalog(catalog)
    knowledge = role_behaviours.validate_knowledge_base(knowledge)
    plan = role_evidence_planning.build_role_evidence_collection_plan(tactic, catalog, knowledge, aliases)
    records_by_role = _records_by_role(knowledge, catalog)
    output = []
    for plan_role in plan["leicester_roles"]:
        role_id = plan_role["role_internal_id"]
        records = records_by_role.get(role_id, [])
        if not records:
            continue
        semantics = _semantic_items(records)
        ers = expected_role_space.build_expected_role_space(role_id, "IP", catalog, knowledge)["expected_role_space"]
        do_not = []
        for item in semantics:
            if item["semantic_id"] in _DO_NOT_REINFER:
                do_not.append(_DO_NOT_REINFER[item["semantic_id"]])
        for record in records:
            if record["behaviour_id"] in _BEHAVIOUR_DO_NOT_REINFER:
                do_not.append(_BEHAVIOUR_DO_NOT_REINFER[record["behaviour_id"]])
        analysis_gap, evidence_claim_missing = _gap_fields(plan_role)
        output.append({
            "role_internal_id": role_id,
            "existing_evidence_ids": sorted({evidence_id for record in records for evidence_id in record["evidence_ids"]}),
            "existing_supported_claims": [{
                "behaviour_id": record["behaviour_id"], "claim": record["description_ko"],
                "evidence_ids": copy.deepcopy(record["evidence_ids"]), "verification": record["verification"],
            } for record in records],
            "existing_semantics": semantics,
            "existing_ers": [{"field": field, **copy.deepcopy(item)} for field in _FIELDS for item in ers[field]],
            "recheck_existing_evidence_first": True,
            "missing_analysis_evidence": {
                "analysis_gap": analysis_gap,
                "evidence_claim_missing": evidence_claim_missing,
            },
            "additional_capture": {
                "required": False,
                "reason": [],
                "requested_content": [],
            },
            "do_not_reinfer": sorted(set(do_not)),
        })
    return {
        "manifest_type": "read_only_evidence_request_manifest",
        "limitations": [
            "Existing evidence IDs are reported first and are not requested again.",
            "Existing imported, user-reviewed and official evidence must be rechecked before any additional capture is considered.",
            "additional_capture is required only when recorded evidence is actually truncated, the claim matters to current analysis, and no other source covers it.",
            "The manifest does not create behaviour, semantic, ERS, compatibility, or edge data.",
        ],
        "evidence_acquisition_order": [
            "existing_imported_evidence_reuse",
            "existing_user_provided_reviewed_evidence_recheck",
            "existing_official_evidence_recheck",
            "additional_capture_only_when_required",
        ],
        "roles": output,
        "leicester_oop_input": copy.deepcopy(plan["leicester_oop_input"]),
    }
