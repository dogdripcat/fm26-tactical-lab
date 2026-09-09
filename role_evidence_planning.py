"""Read-only evidence collection planning from existing role and graph coverage.

This module ranks collection batches categorically. It creates no behaviour,
semantic, ERS, or compatibility data and does not modify Connectivity output.
"""
from __future__ import annotations

import copy
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

import connectivity_engine
import expected_role_space
import role_behaviours
import role_connectivity_readiness
import role_constraints
import role_knowledge_coverage


COMPLETENESS = ("semantic_complete", "mixed", "compatibility_only", "evidence_missing")
GROUPS = ("send", "receive", "space", "movement")


def _empty_exposure() -> Dict[str, Dict[str, int]]:
    return {direction: {kind: 0 for kind in COMPLETENESS} for direction in ("source", "target")}


def _edge_eligible_semantics(knowledge: List[Dict[str, Any]], catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """Read existing mappings only; never infer a semantic from a role name."""
    result: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: {group: [] for group in GROUPS})
    for record in role_behaviours.behaviour_records(knowledge, catalog):
        if not record["role_internal_id"] or record["verification"] not in ("verified", "official", "user_ingame_verified"):
            continue
        for group, items in record["connectivity_semantics"].items():
            for item in items:
                if item.get("edge_eligible") is False or item.get("verification") not in ("verified", "official", "user_ingame_verified"):
                    continue
                result[record["role_internal_id"]][group].append(item["semantic_id"])
    return {role_id: {group: sorted(set(values)) for group, values in groups.items()} for role_id, groups in result.items()}


def _gaps(exposure: Dict[str, Dict[str, int]], semantic_groups: Dict[str, List[str]], ers_status: str) -> List[str]:
    gaps = []
    if exposure["source"]["evidence_missing"] and not semantic_groups["send"]:
        gaps.append("source evidence_missing edge에 대응하는 edge-eligible send semantic 근거 없음")
    if exposure["target"]["evidence_missing"] and not semantic_groups["receive"]:
        gaps.append("target evidence_missing edge에 대응하는 edge-eligible receive semantic 근거 없음")
    if ers_status == "unknown":
        gaps.append("검증된 ERS ontology mapping 결과 없음")
    return gaps


def _tier(exposure: Dict[str, Dict[str, int]], semantic_groups: Dict[str, List[str]],
          behaviour_status: str, ers_status: str, shared_identity: bool, used: bool) -> str:
    """Categorical order from declared coverage factors only; never a role-importance heuristic."""
    missing = exposure["source"]["evidence_missing"] + exposure["target"]["evidence_missing"]
    semantic_absent = not any(semantic_groups[group] for group in GROUPS)
    coverage_gap = behaviour_status in ("identity_only", "unresolved") or semantic_absent or ers_status == "unknown"
    if used and missing and (coverage_gap or shared_identity):
        return "A"
    if used and missing:
        return "B"
    return "C"


def build_role_evidence_collection_plan(tactic: Dict[str, Any], catalog: List[Dict[str, Any]],
                                        knowledge: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str]) -> Dict[str, Any]:
    """Return a JSON-compatible, deterministic collection plan without analysis changes."""
    catalog = role_constraints.validate_role_catalog(catalog)
    knowledge = role_behaviours.validate_knowledge_base(knowledge)
    tactic_copy = copy.deepcopy(tactic)
    graph = connectivity_engine.build_connectivity(tactic_copy, catalog, knowledge, aliases)
    coverage = role_knowledge_coverage.build_coverage_report(catalog, knowledge)
    coverage_by_id = {item["internal_id"]: item for item in coverage["roles"]}
    readiness_by_id = {item["role_internal_id"]: item["analysis_readiness"]["connectivity"]
                       for item in role_connectivity_readiness.build_analysis_readiness(catalog, knowledge)}
    edge_semantics = _edge_eligible_semantics(knowledge, catalog)
    catalog_by_id = {item["internal_id"]: item for item in catalog}
    node_by_id = {item["node_id"]: item for item in graph["nodes"]}
    exposure = defaultdict(_empty_exposure)
    role_nodes = defaultdict(list)
    role_families = defaultdict(set)
    for node in graph["nodes"]:
        role_id = node["role_internal_id"]
        if role_id is None:
            continue
        role_nodes[role_id].append(node)
        role_families[role_id].add(node.get("position_family", "unknown"))
    for edge in graph["edges"]:
        completeness = edge["provenance"]["evidence_completeness"]
        for direction, node_id in (("source", edge["from_node_id"]), ("target", edge["to_node_id"])):
            role_id = node_by_id[node_id]["role_internal_id"]
            if role_id is not None:
                exposure[role_id][direction][completeness] += 1
    role_rows = []
    for role_id in sorted(role_nodes):
        role = catalog_by_id[role_id]
        ers = expected_role_space.build_expected_role_space(role_id, "IP", catalog, knowledge)["expected_role_space"]
        edge_groups = edge_semantics.get(role_id, {group: [] for group in GROUPS})
        row_exposure = copy.deepcopy(exposure[role_id])
        row = {
            "role_internal_id": role_id,
            "phase": "IP",
            "role_name_ko": role["role_name_ko"],
            "configured_nodes": [node["node_id"] for node in role_nodes[role_id]],
            "configured_positions": [node["configured_position"] for node in role_nodes[role_id]],
            "configured_position_families": sorted(role_families[role_id]),
            "shared_role_identity": len(role_nodes[role_id]) > 1,
            "source_target_edge_exposure": row_exposure,
            "behaviour_coverage": coverage_by_id[role_id]["status"],
            "semantic_coverage": readiness_by_id[role_id],
            "edge_eligible_semantics": edge_groups,
            "ers_status": ers["status"],
            "evidence_gaps": _gaps(row_exposure, edge_groups, ers["status"]),
        }
        row["priority_tier"] = _tier(
            row_exposure, edge_groups, row["behaviour_coverage"], row["ers_status"],
            row["shared_role_identity"], True,
        )
        role_rows.append(row)
    resolved = [node for node in graph["nodes"] if node["role_internal_id"] is not None]
    unresolved = [node for node in graph["nodes"] if node["role_internal_id"] is None]
    oop_rows = [
        {"role_internal_id": role["internal_id"], "role_name_ko": role["role_name_ko"],
         "behaviour_coverage": coverage_by_id[role["internal_id"]]["status"],
         "available_starting_positions": copy.deepcopy(role["available_starting_positions"])}
        for role in catalog if role["phase"] == "OOP"
    ]
    unused_ip = [role["internal_id"] for role in catalog if role["phase"] == "IP" and role["internal_id"] not in role_nodes]
    tiers = {
        "A": [row["role_internal_id"] for row in role_rows if row["priority_tier"] == "A"],
        "B": [row["role_internal_id"] for row in role_rows if row["priority_tier"] == "B"],
        "C": unused_ip,
    }
    return {
        "planner": "read_only_role_evidence_coverage",
        "limitations": [
            "Priority tiers are categorical collection order, not numeric tactical scores.",
            "No behaviour, semantic, ERS, compatibility, edge state, or role effect is inferred or created.",
            "Edge exposure counts identify evidence gaps; they do not predict passes or performance.",
        ],
        "leicester_ip_resolution": {
            "configured_roles": len(graph["nodes"]), "resolved_roles": len(resolved), "unresolved_roles": len(unresolved),
            "resolved_node_ids": [node["node_id"] for node in resolved],
        },
        "leicester_oop_input": {
            "configured_entries": len(tactic_copy.get("oop_roles", {})) if isinstance(tactic_copy.get("oop_roles", {}), dict) else 0,
            "raw_roles": copy.deepcopy(tactic_copy.get("oop_roles", {})) if isinstance(tactic_copy.get("oop_roles", {}), dict) else "unknown",
            "resolved_roles": 0,
            "status": "not_available_to_ip_connectivity_graph",
            "limitations": ["The current Connectivity graph intentionally contains IP nodes only.", "OOP tokens are not resolved by this read-only IP graph."],
        },
        "connectivity_regression_snapshot": {
            "edges": len(graph["edges"]),
            **copy.deepcopy(graph["evidence_completeness"]),
            "progression_chain_statuses": dict(Counter(item["status"] for item in graph["progression_chains"])),
            "isolated_nodes": len(graph["isolated_nodes"]),
        },
        "leicester_roles": role_rows,
        "priority_tiers": tiers,
        "screenshot_batches": {
            "batch_1": {"tier": "A", "role_internal_ids": tiers["A"], "purpose": "Leicester configured core-line roles with evidence_missing exposure."},
            "batch_2": {"tier": "B", "role_internal_ids": tiers["B"], "purpose": "Remaining Leicester IP roles with evidence_missing exposure."},
            "batch_3": {"tier": "C", "role_internal_ids": unused_ip, "purpose": "IP catalogue roles not represented in the current Leicester graph."},
        },
        "oop_gap": {"roles_total": len(oop_rows), "roles": oop_rows, "coverage": coverage["by_phase"]["OOP"]},
        "global_coverage": {
            "roles_total": coverage["total_roles"],
            "by_phase": coverage["by_phase"],
            "by_role_family": coverage["by_role_family"],
            "behaviour_status_totals": {key: coverage[key] for key in ("verified", "partial", "identity_only", "unresolved")},
            "ers_coverage": expected_role_space.expected_role_space_coverage(catalog, knowledge),
        },
    }
