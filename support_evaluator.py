"""Structural Support Phase 1 over frozen Connectivity and Progression outputs.

This evaluator deliberately consumes an existing graph.  It never creates or
removes Connectivity links and never decides whether an edge advances play.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Dict, Iterable, List


_REGIONS = ("left", "centre", "right")
_OPTION_KEYS = ("forward", "lateral", "recycle", "inside", "outside")
_PRIMARY_DIRECTIONS = ("forward", "lateral", "recycle")
_ROLE_CLASSES = {
    "receive_between_lines": "receiving_support_interpretation",
    "receive_centrally": "receiving_support_interpretation",
    "move_to_receive": "support_position_interpretation",
    "support_central_passing_links": "distribution_support_interpretation",
    "send_simple_pass": "distribution_support_interpretation",
    "send_forward": "distribution_support_interpretation",
    "hold_width": "structural_space_interpretation",
    "move_inside": "structural_space_interpretation",
    "open_space_for_fullback": "structural_space_interpretation",
}


def _index(nodes: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {node["node_id"]: node for node in nodes}


def _row(link: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "link_id": link["link_id"], "target_id": target["node_id"],
        "configured_position": target.get("configured_position"),
        "band": target.get("vertical_band"), "region": target.get("lateral_slot"),
    }


def _options(receiver: Dict[str, Any], links: List[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    options = {key: [] for key in _OPTION_KEYS}
    for link in links:
        if link.get("source") != receiver["node_id"]:
            continue
        target = by_id.get(link.get("target"))
        if target is None:
            continue
        row = _row(link, target)
        source_index, target_index = receiver.get("vertical_index"), target.get("vertical_index")
        if link.get("direction") == "forward" and isinstance(source_index, int) and isinstance(target_index, int) and target_index > source_index:
            options["forward"].append(row)
        elif link.get("direction") == "backward" and isinstance(source_index, int) and isinstance(target_index, int) and target_index < source_index:
            options["recycle"].append(row)
        elif link.get("direction") == "support" and source_index == target_index:
            options["lateral"].append(row)
        source_region, target_region = receiver.get("lateral_slot"), target.get("lateral_slot")
        if source_region in {"left", "right"} and target_region == "centre":
            options["inside"].append(row)
        elif source_region == "centre" and target_region in {"left", "right"}:
            options["outside"].append(row)
    for values in options.values():
        values.sort(key=lambda item: (item["link_id"], item["target_id"]))
    return options


def _direction_set(options: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """Primary physical continuation directions; inside/outside remain descriptors."""
    return [key for key in _PRIMARY_DIRECTIONS if options[key]]


def _terminal(node: Dict[str, Any], endpoints: set[str], highest_index: int | None) -> bool:
    """A terminal is only a configured forward-band endpoint on the highest occupied line."""
    return bool(highest_index is not None and node.get("vertical_index") == highest_index
                and node.get("vertical_band") == "forward" and node["node_id"] in endpoints)


def _receivers(v2: Dict[str, Any], links: List[Dict[str, Any]]) -> List[str]:
    ids = {link["target"] for link in links}
    for route in v2.get("progression_routes", []):
        ids.update(route.get("node_ids", [])[1:-1])
    return sorted(ids)


def _profile(node: Dict[str, Any], links: List[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]], endpoints: set[str], highest_index: int | None) -> Dict[str, Any]:
    options = _options(node, links, by_id)
    directions = _direction_set(options)
    unique_links = {item["link_id"] for values in options.values() for item in values}
    terminal = _terminal(node, endpoints, highest_index)
    return {
        "receiver_id": node["node_id"], "configured_position": node.get("configured_position"),
        "band": node.get("vertical_band"), "region": node.get("lateral_slot"),
        "inbound_structural_context": sorted(link["link_id"] for link in links if link.get("target") == node["node_id"]),
        "terminal_endpoint": terminal, "support_options": options, "support_directions": directions,
        "single_option_support": len(unique_links) == 1,
        "support_isolated": not terminal and not unique_links,
        "support_dependencies": [], "role_adjustments": [],
    }


def _dependencies(profiles: List[Dict[str, Any]], links: List[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]], endpoints: set[str], highest_index: int | None) -> List[Dict[str, Any]]:
    rows = []
    for profile in profiles:
        receiver = by_id[profile["receiver_id"]]
        candidates = sorted({item["target_id"] for values in profile["support_options"].values() for item in values if item["target_id"] != receiver["node_id"]})
        for support_node in candidates:
            remaining = [link for link in links if link.get("source") != support_node and link.get("target") != support_node]
            after = _profile(receiver, remaining, by_id, endpoints, highest_index)
            before = profile["support_directions"]
            after_directions = after["support_directions"]
            lost = [direction for direction in before if direction not in after_directions]
            if lost or (not profile["support_isolated"] and after["support_isolated"]):
                rows.append({
                    "dependent_receiver": receiver["node_id"], "support_node": support_node,
                    "lost_support_categories": lost,
                    "becomes_support_isolated": not profile["support_isolated"] and after["support_isolated"],
                    "before_directions": before, "after_directions": after_directions,
                    "limitation": "Removal compares existing structural continuation categories only; it does not predict substitutions or execution.",
                })
    return sorted(rows, key=lambda item: (item["dependent_receiver"], item["support_node"]))


def _role_adjustments(v2: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for node in v2.get("role_modifiers", []):
        for item in node.get("items", []):
            classification = _ROLE_CLASSES.get(item.get("semantic_id"))
            if classification:
                rows.append({
                    "receiver_id": node["node_id"], "semantic_id": item["semantic_id"],
                    "classification": classification, "behaviour_id": item.get("behaviour_id"),
                    "evidence_ids": sorted(item.get("evidence_ids", [])),
                    "limitation": "Role semantics annotate existing support structure and never create links, dependencies, or terminal status.",
                })
    return sorted(rows, key=lambda item: (item["receiver_id"], item["semantic_id"], item["behaviour_id"] or ""))


def evaluate_support(connectivity_v2: Dict[str, Any], progression_evaluation: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Describe post-reception structural continuation without producing a graph or score."""
    v2 = copy.deepcopy(connectivity_v2)
    nodes = v2.get("nodes", [])
    by_id = _index(nodes)
    links = [link for link in v2.get("structural_links", []) if link.get("source") in by_id and link.get("target") in by_id]
    endpoints = {route.get("node_ids", [])[-1] for route in v2.get("progression_routes", []) if route.get("node_ids")}
    indexes = [node.get("vertical_index") for node in nodes if isinstance(node.get("vertical_index"), int)]
    highest_index = max(indexes) if indexes else None
    profiles = [_profile(by_id[node_id], links, by_id, endpoints, highest_index) for node_id in _receivers(v2, links) if node_id in by_id]
    dependencies = _dependencies(profiles, links, by_id, endpoints, highest_index)
    dependency_by_receiver = defaultdict(list)
    for row in dependencies:
        dependency_by_receiver[row["dependent_receiver"]].append(copy.deepcopy(row))
    for profile in profiles:
        profile["support_dependencies"] = dependency_by_receiver[profile["receiver_id"]]
    events = (progression_evaluation or {}).get("advancement_events", [])
    if not events:
        events = (progression_evaluation or {}).get("line_skips", [])
        # The public evaluator stores all advancement events in observations only; derive no new
        # event here.  Route-profile events are the explicit read-only fallback.
        events = [event for profile in (progression_evaluation or {}).get("route_profiles", []) for event in profile.get("advancement_events", [])] or events
    events = list({event.get("link_id"): event for event in events if event.get("link_id")}.values())
    profile_by_id = {profile["receiver_id"]: profile for profile in profiles}
    advance_then_support = []
    for event in sorted(events, key=lambda item: item.get("link_id", "")):
        profile = profile_by_id.get(event.get("target"))
        if profile is None:
            continue
        advance_then_support.append({
            "receiver_id": profile["receiver_id"], "advancement_origin": event.get("source"),
            "advancement_link_id": event.get("link_id"), "forward_continuation": bool(profile["support_options"]["forward"]),
            "lateral_continuation": bool(profile["support_options"]["lateral"]),
            "recycle_continuation": bool(profile["support_options"]["recycle"]),
            "support_directions": profile["support_directions"], "terminal_endpoint": profile["terminal_endpoint"],
            "support_isolated": profile["support_isolated"], "support_dependencies": profile["support_dependencies"],
        })
    regional = {}
    for region in _REGIONS:
        rows = [profile for profile in profiles if profile["region"] == region]
        regional[region] = {
            "receiving_states": [row["receiver_id"] for row in rows],
            "receivers_with_forward_support": [row["receiver_id"] for row in rows if row["support_options"]["forward"]],
            "receivers_with_lateral_support": [row["receiver_id"] for row in rows if row["support_options"]["lateral"]],
            "receivers_with_recycle": [row["receiver_id"] for row in rows if row["support_options"]["recycle"]],
            "support_isolations": [row["receiver_id"] for row in rows if row["support_isolated"]],
            "single_option_receivers": [row["receiver_id"] for row in rows if row["single_option_support"]],
            "cross_region_support_available": any(row["support_options"]["inside"] or row["support_options"]["outside"] for row in rows),
        }
    return {
        "receiving_states": profiles, "regional_support": regional,
        "support_isolations": [row["receiver_id"] for row in profiles if row["support_isolated"]],
        "single_option_receivers": [row["receiver_id"] for row in profiles if row["single_option_support"]],
        "support_dependencies": dependencies, "advance_then_support": advance_then_support,
        "role_adjustments": _role_adjustments(v2),
        "observations": [
            {"type": "receiving_states", "node_ids": [row["receiver_id"] for row in profiles]},
            {"type": "terminal_endpoints", "node_ids": [row["receiver_id"] for row in profiles if row["terminal_endpoint"]]},
        ],
        "limitations": [
            "Consumes frozen Connectivity v2 links and Progression advancement context only; it does not construct a graph or decide reachability.",
            "Continuation categories are structural descriptions, not support quality, pass success, possession safety, or press resistance.",
            "Player attributes, Team Instruction effects, third-man patterns, partnerships, penetration, chance creation, and goal threat are unmodelled.",
        ],
    }
