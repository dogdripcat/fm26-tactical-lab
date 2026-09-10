"""Evidence-only IP connectivity candidates; no role scores or match predictions."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

import role_constraints
import role_behaviours
import positional_relationships


PATH_TYPES = frozenset((
    "defence_to_midfield", "midfield_to_attacking_midfield",
    "attacking_midfield_to_forward", "centre_to_wide", "wide_to_centre",
))
STATES = frozenset(("connected", "weakly_connected", "structurally_unsupported", "unknown"))

# These are generic meanings of existing behaviour categories, not role-specific rules.
SENDER_CATEGORIES = frozenset(("passing", "link_play", "chance_creation"))
RECEIVER_CATEGORIES = frozenset(("ball_receiving", "link_play"))


def _position_zone(position: str) -> str:
    if not isinstance(position, str):
        return "unknown"
    if positional_relationships.configured_position_alias_status(position) == "unresolved":
        return "unknown"
    position = positional_relationships.normalize_configured_position(position) or position
    if position in {"GK", "LCB", "CB", "RCB", "DC", "D(C)"}:
        return "defence"
    if position in {"DML", "DM", "DMR", "MCL", "MC", "MCR", "CM"}:
        return "midfield"
    if position in {"AMC", "AM"}:
        return "attacking_midfield"
    if position in {"ST", "CF"}:
        return "forward"
    if position in {"LB", "RB", "DL", "DR", "AML", "AMR", "ML", "MR", "WL", "WR", "wing_back_left", "wing_back_right"}:
        return "wide"
    return "unknown"


def _path_type(source_zone: str, target_zone: str) -> str | None:
    mapping = {
        ("defence", "midfield"): "defence_to_midfield",
        ("midfield", "attacking_midfield"): "midfield_to_attacking_midfield",
        ("attacking_midfield", "forward"): "attacking_midfield_to_forward",
        ("defence", "wide"): "centre_to_wide",
        ("midfield", "wide"): "centre_to_wide",
        ("attacking_midfield", "wide"): "centre_to_wide",
        ("wide", "defence"): "wide_to_centre",
        ("wide", "midfield"): "wide_to_centre",
        ("wide", "attacking_midfield"): "wide_to_centre",
        ("wide", "forward"): "wide_to_centre",
    }
    return mapping.get((source_zone, target_zone))


def _index_by_phase_and_abbr(catalog: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    index: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for role in catalog:
        if role["display_abbr"]:
            index.setdefault((role["phase"], role["display_abbr"]), []).append(role)
    return index


def build_connectivity(tactic: Dict[str, Any], catalog: List[Dict[str, Any]], behaviour_kb: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str]) -> Dict[str, Any]:
    """Build directional candidates from verified IP behaviour descriptions only."""
    behaviour_kb = role_behaviours.validate_knowledge_base(behaviour_kb)
    resolved_catalog = role_constraints.resolve_catalog(catalog, behaviour_kb)
    by_abbr = _index_by_phase_and_abbr(resolved_catalog)
    semantics = _semantic_index(behaviour_kb, catalog)
    nodes = _build_ip_nodes(tactic, by_abbr, aliases, semantics)
    edges = _build_edges(nodes)
    chains = _progression_chains(nodes, edges)
    isolated = _isolated_nodes(nodes, edges)
    return {
        "nodes": nodes,
        "edges": edges,
        "progression_chains": chains,
        "isolated_nodes": isolated,
        "evidence_completeness": evidence_completeness_summary(edges),
        "limitations": [
            "IP configuration only; OOP roles are not mixed into this graph.",
            "Edges are role-description candidates, not observed or predicted passes.",
            "No pass frequency, distance, success rate, player location or numeric score is inferred.",
            "Only the five declared path types are emitted.",
        ],
    }


def _semantic_index(behaviour_kb: List[Dict[str, Any]], catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    index: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for record in role_behaviours.behaviour_records(behaviour_kb, catalog):
        internal_id = record['role_internal_id']
        if internal_id is None:
            continue
        groups = index.setdefault(internal_id, {'send': [], 'receive': [], 'space': [], 'movement': []})
        for group, items in record['connectivity_semantics'].items():
            for item in items:
                if item.get('edge_eligible') is False:
                    continue
                groups[group].append({
                    'behaviour_id': record['behaviour_id'],
                    'semantic_id': item['semantic_id'],
                    'evidence_ids': copy.deepcopy(item['evidence_ids']),
                    'verification': item['verification'],
                })
    return index


def _build_ip_nodes(tactic: Dict[str, Any], by_abbr: Dict[Tuple[str, str], List[Dict[str, Any]]], aliases: Dict[Tuple[str, str], str], semantics: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[Dict[str, Any]]:
    roles = tactic.get("ip_roles", {})
    if not isinstance(roles, dict):
        return []
    nodes = []
    for position, raw_role in roles.items():
        normalized_position = positional_relationships.normalize_configured_position(position) or position
        canonical = aliases.get(("IP", raw_role), raw_role) if isinstance(raw_role, str) else raw_role
        candidates = by_abbr.get(("IP", canonical), []) if isinstance(canonical, str) else []
        if len(candidates) != 1:
            node = {
                "node_id": f"IP:{normalized_position}", "phase": "IP", "configured_position": normalized_position,
                "role_internal_id": None,
                "resolved_role": {"status": "unresolved", "raw_value": raw_role},
                "evidence_ids": [],
            }
            nodes.append(_with_configured_position(node))
            continue
        role = candidates[0]
        node = {
            "node_id": f"IP:{normalized_position}", "phase": "IP", "configured_position": normalized_position,
            "role_internal_id": role["internal_id"],
            "resolved_role": {
                "status": "resolved", "role_name_ko": role["role_name_ko"],
                "display_abbr": role["display_abbr"],
            },
            "role_tags": copy.deepcopy(role["role_tags"]),
            "described_behaviours": copy.deepcopy(role["described_behaviours"]),
            "connectivity_semantics": copy.deepcopy(semantics.get(role['internal_id'], {'send': [], 'receive': [], 'space': [], 'movement': []})),
            "evidence_ids": [item["evidence_id"] for item in role["evidence"]],
        }
        nodes.append(_with_configured_position(node))
    return nodes


def _with_configured_position(node: Dict[str, Any]) -> Dict[str, Any]:
    """Attach read-only registry facts without using them in connectivity logic."""
    position_node = positional_relationships.build_position_node(
        node["phase"], node["configured_position"], node.get("role_internal_id"),
    )
    for key in ("position_family", "vertical_band", "vertical_index", "lateral_slot", "expected_role_space"):
        node[key] = position_node[key]
    return node


def _build_edges(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = []
    for source in nodes:
        for target in nodes:
            if source["node_id"] == target["node_id"]:
                continue
            path_type = _path_type(_position_zone(source["configured_position"]), _position_zone(target["configured_position"]))
            if path_type is None:
                continue
            edges.append(_edge(source, target, path_type))
    return edges


def _edge(source: Dict[str, Any], target: Dict[str, Any], path_type: str) -> Dict[str, Any]:
    source_unresolved = source["role_internal_id"] is None
    target_unresolved = target["role_internal_id"] is None
    source_behaviours = source.get("described_behaviours", [])
    target_behaviours = target.get("described_behaviours", [])
    source_support = [item for item in source_behaviours if item["category"] in SENDER_CATEGORIES]
    target_support = [item for item in target_behaviours if item["category"] in RECEIVER_CATEGORIES]
    source_semantics = source.get('connectivity_semantics', {}).get('send', [])
    target_semantics = target.get('connectivity_semantics', {}).get('receive', [])
    # Semantics are authoritative for their own group.  Existing category evidence
    # remains the compatibility path when no explicit mapping exists for that side.
    source_basis = source_semantics or _basis(source_support)
    target_basis = target_semantics or _basis(target_support)
    source_evidence = source_semantics or source_support
    target_evidence = target_semantics or target_support
    source_method = "semantic" if source_semantics else "compatibility" if source_support else "none"
    target_method = "semantic" if target_semantics else "compatibility" if target_support else "none"
    if source_unresolved or target_unresolved or not source_behaviours or not target_behaviours:
        status = "unknown"
    elif _has_explicit_structural_block(source_behaviours + target_behaviours, path_type):
        status = "structurally_unsupported"
    elif source_basis and target_basis:
        status = "connected"
    elif source_basis or target_basis:
        status = "weakly_connected"
    else:
        # Behaviour descriptions do not say this route is impossible. Absence is unknown.
        status = "unknown"
    evidence_ids = sorted({evidence_id for item in source_evidence + target_evidence for evidence_id in item["evidence_ids"]})
    provenance = _provenance(source_method, target_method, source_basis, target_basis, evidence_ids)
    position_relation = positional_relationships.calculate_configured_position_relation(source, target)
    return {
        "edge_id": f"{source['node_id']}->{target['node_id']}",
        "from_node_id": source["node_id"], "to_node_id": target["node_id"],
        "from_node": source["node_id"], "to_node": target["node_id"], "phase": "IP",
        "path_type": path_type, "connection_type": path_type, "status": status,
        "source_basis": source_basis, "target_basis": target_basis,
        "basis": {"source": source_basis, "target": target_basis},
        "evidence_ids": evidence_ids,
        "provenance": provenance,
        "configured_position_relation": position_relation["configured_position_relation"],
        "limitations": ["Direction is a connectivity candidate only; no actual pass is observed."],
    }


def _provenance(source_method: str, target_method: str, source_basis: List[Dict[str, Any]], target_basis: List[Dict[str, Any]], evidence_ids: List[str]) -> Dict[str, Any]:
    """Describe evidence path only; it never changes the edge result."""
    methods = {source_method, target_method}
    if methods == {"semantic"}:
        completeness = "semantic_complete"
    elif "semantic" in methods and "compatibility" in methods:
        completeness = "mixed"
    elif methods == {"compatibility"}:
        completeness = "compatibility_only"
    else:
        completeness = "evidence_missing"
    items = source_basis + target_basis
    return {
        "source_method": source_method,
        "target_method": target_method,
        "semantic_ids": sorted({item["semantic_id"] for item in items if item.get("semantic_id")}),
        "behaviour_ids": sorted({item["behaviour_id"] for item in items if item.get("behaviour_id")}),
        "evidence_ids": list(evidence_ids),
        "evidence_completeness": completeness,
    }


def evidence_completeness_summary(edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count provenance paths for compatibility retirement planning, without scoring."""
    summary = {"edges_total": len(edges), "semantic_complete": 0, "mixed": 0,
               "compatibility_only": 0, "evidence_missing": 0}
    for edge in edges:
        completeness = edge.get("provenance", {}).get("evidence_completeness", "evidence_missing")
        summary[completeness] += 1
    return summary


def _basis(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"behaviour_id": item["behaviour_id"], "evidence_ids": item["evidence_ids"]} for item in items]


def _has_explicit_structural_block(behaviours: List[Dict[str, Any]], path_type: str) -> bool:
    """Reserved evidence-backed metadata; no current FM26 role data uses it."""
    return any(
        item.get("connectivity_effect") == "structurally_unsupported"
        and path_type in item.get("connection_types", [])
        for item in behaviours
    )


def _progression_chains(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_pair = {(edge["from_node_id"], edge["to_node_id"]): edge for edge in edges}
    groups = {zone: [node for node in nodes if _position_zone(node["configured_position"]) == zone]
              for zone in ("defence", "midfield", "attacking_midfield", "forward")}
    chains = []
    for defence in groups["defence"]:
        for midfield in groups["midfield"]:
            for attacking_midfield in groups["attacking_midfield"]:
                for forward in groups["forward"]:
                    links = [
                        by_pair[(defence["node_id"], midfield["node_id"])],
                        by_pair[(midfield["node_id"], attacking_midfield["node_id"])],
                        by_pair[(attacking_midfield["node_id"], forward["node_id"])],
                    ]
                    statuses = [link["status"] for link in links]
                    if "structurally_unsupported" in statuses:
                        status = "broken_progression_chain"
                    elif "unknown" in statuses:
                        status = "unknown_chain"
                    elif "weakly_connected" in statuses:
                        status = "weak_progression_chain"
                    else:
                        status = "connected"
                    chains.append({
                        "chain_id": "->".join((defence["node_id"], midfield["node_id"], attacking_midfield["node_id"], forward["node_id"])),
                        "node_ids": [defence["node_id"], midfield["node_id"], attacking_midfield["node_id"], forward["node_id"]],
                        "status": status,
                        "edge_ids": [link["edge_id"] for link in links],
                    })
    return chains


def _isolated_nodes(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []
    for node in nodes:
        relevant = [edge for edge in edges if node["node_id"] in (edge["from_node_id"], edge["to_node_id"])]
        usable = [edge for edge in relevant if edge["status"] in ("connected", "weakly_connected")]
        if usable:
            continue
        output.append({
            "node_id": node["node_id"],
            "status": "unknown" if not relevant or any(edge["status"] == "unknown" for edge in relevant) else "isolated_node",
            "edge_ids": [edge["edge_id"] for edge in relevant],
        })
    return output
