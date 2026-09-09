"""Read-only evidence sufficiency metadata for the configured IP roles of one tactic."""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import expected_role_space
import role_behaviours
import role_constraints
import role_evidence_planning


GROUPS = ("send", "receive", "space", "movement")
FIELDS = ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions")
VERIFIED = frozenset(("verified", "official", "user_ingame_verified"))
# These are direct, narrow interpretations of already verified behaviour IDs.
# They are not role-name rules and do not affect Connectivity.
DIRECT_BEHAVIOUR_CAPABILITIES = {
    "CB_IP_SUPPORT_POSSESSION": "can_support_generic_possession_support_analysis",
}


def _records_by_role(knowledge: List[Dict[str, Any]], catalog: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    output: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in role_behaviours.behaviour_records(knowledge, catalog):
        if record["role_internal_id"] and record["verification"] in VERIFIED and record["evidence_ids"]:
            output[record["role_internal_id"]].append(record)
    return output


def _semantic_groups(records: List[Dict[str, Any]]) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
    all_items = {group: [] for group in GROUPS}
    eligible_items = {group: [] for group in GROUPS}
    for record in records:
        for group, semantics in record["connectivity_semantics"].items():
            for semantic in semantics:
                if semantic.get("verification") not in VERIFIED or not semantic.get("evidence_ids"):
                    continue
                item = {
                    "semantic_id": semantic["semantic_id"], "behaviour_ids": [record["behaviour_id"]],
                    "evidence_ids": copy.deepcopy(semantic["evidence_ids"]),
                    "edge_eligible": semantic.get("edge_eligible") is not False,
                }
                all_items[group].append(item)
                if item["edge_eligible"]:
                    eligible_items[group].append(item)
    return all_items, eligible_items


def _capabilities(records: List[Dict[str, Any]], all_semantics: Dict[str, List[Dict[str, Any]]],
                  eligible: Dict[str, List[Dict[str, Any]]], ers: Dict[str, Any]) -> List[str]:
    output = []
    if eligible["send"]:
        output.append("can_support_distribution_analysis")
    if eligible["receive"]:
        output.append("can_support_reception_analysis")
    if ers["occupancy"]:
        output.append("can_support_space_occupation_analysis")
    if all_semantics["movement"]:
        output.append("can_support_movement_behaviour_analysis")
    if ers["structural_effects"]:
        output.append("can_support_structural_support_analysis")
    for record in records:
        if record["behaviour_type"] == "goal_threat":
            output.append("can_support_goal_threat_behavioural_analysis")
        capability = DIRECT_BEHAVIOUR_CAPABILITIES.get(record["behaviour_id"])
        if capability:
            output.append(capability)
    return sorted(set(output))


def _unsafe(all_semantics: Dict[str, List[Dict[str, Any]]], eligible: Dict[str, List[Dict[str, Any]]],
            ers: Dict[str, Any]) -> List[str]:
    output = []
    if not eligible["send"]:
        output.append("cannot_infer_edge_eligible_distribution")
    if not eligible["receive"]:
        output.append("cannot_infer_connectivity_reception")
    if ers["status"] == "unknown":
        output.append("cannot_infer_expected_role_space")
    for group, items in all_semantics.items():
        for item in items:
            if not item["edge_eligible"]:
                output.append(f"{item['semantic_id']}_does_not_support_connectivity_edge_inference")
    return sorted(set(output))


def build_current_tactic_evidence_sufficiency(tactic: Dict[str, Any], catalog: List[Dict[str, Any]],
                                               knowledge: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str]) -> Dict[str, Any]:
    """Report current evidence capability only; it neither applies nor changes any rule."""
    catalog = role_constraints.validate_role_catalog(catalog)
    knowledge = role_behaviours.validate_knowledge_base(knowledge)
    plan = role_evidence_planning.build_role_evidence_collection_plan(tactic, catalog, knowledge, aliases)
    records_by_role = _records_by_role(knowledge, catalog)
    catalog_by_id = {role["internal_id"]: role for role in catalog}
    rows = []
    for plan_row in plan["leicester_roles"]:
        role_id = plan_row["role_internal_id"]
        records = records_by_role[role_id]
        all_semantics, eligible = _semantic_groups(records)
        ers = expected_role_space.build_expected_role_space(role_id, "IP", catalog, knowledge)["expected_role_space"]
        capabilities = _capabilities(records, all_semantics, eligible, ers)
        rows.append({
            "role_internal_id": role_id,
            "role_name_ko": catalog_by_id[role_id]["role_name_ko"],
            "configured_positions": copy.deepcopy(plan_row["configured_positions"]),
            "evidence_ids": sorted({evidence_id for record in records for evidence_id in record["evidence_ids"]}),
            "behaviour_coverage": plan_row["behaviour_coverage"],
            "semantic_groups_supported": all_semantics,
            "ers_supported": {field: copy.deepcopy(ers[field]) for field in FIELDS},
            "safe_analysis_capabilities": capabilities,
            "unsafe_inferences": _unsafe(all_semantics, eligible, ers),
            "limitations": [
                "Capabilities describe only existing verified evidence; they do not change Connectivity edge state.",
                "No actual pass, reception, location, frequency, or performance is observed.",
            ],
        })
    aggregate = {
        "distribution_capable_roles": [], "reception_capable_roles": [],
        "space_occupation_capable_roles": [], "movement_capable_roles": [],
        "structural_effect_capable_roles": [], "roles_with_no_edge_eligible_connectivity_semantic": [],
    }
    capability_keys = {
        "can_support_distribution_analysis": "distribution_capable_roles",
        "can_support_reception_analysis": "reception_capable_roles",
        "can_support_space_occupation_analysis": "space_occupation_capable_roles",
        "can_support_movement_behaviour_analysis": "movement_capable_roles",
        "can_support_structural_support_analysis": "structural_effect_capable_roles",
    }
    for row in rows:
        for capability, key in capability_keys.items():
            if capability in row["safe_analysis_capabilities"]:
                aggregate[key].append(row["role_internal_id"])
        if not any(item["edge_eligible"] for group in row["semantic_groups_supported"].values() for item in group):
            aggregate["roles_with_no_edge_eligible_connectivity_semantic"].append(row["role_internal_id"])
    return {
        "report_type": "current_tactic_evidence_sufficiency",
        "phase": "IP",
        "roles": rows,
        "aggregate": aggregate,
        "limitations": [
            "This is evidence sufficiency metadata, not a tactical quality rating or numeric score.",
            "This report does not apply semantic, ERS, or compatibility rules to Connectivity.",
        ],
    }
