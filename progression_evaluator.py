"""Structural Progression Phase 1, derived solely from frozen Connectivity v2 output.

This module never creates links or routes.  It interprets the configured nodes and
structural links already returned by Connectivity v2.  "Reachable" consequently
means reachable through those existing directed links, not a predicted pass.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

REGIONS = ("left", "centre", "right")


def _ordered_lines(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        index = node.get("vertical_index")
        if isinstance(index, int):
            grouped.setdefault(index, []).append(node)
    return [{
        "vertical_index": index,
        "vertical_band": sorted({n.get("vertical_band", "unknown") for n in rows})[0],
        "node_ids": sorted(n["node_id"] for n in rows),
    } for index, rows in sorted(grouped.items())]


def _gain(source: dict[str, Any], target: dict[str, Any], occupied: list[int]) -> tuple[int, list[int]]:
    source_index, target_index = source.get("vertical_index"), target.get("vertical_index")
    if not isinstance(source_index, int) or not isinstance(target_index, int) or target_index <= source_index:
        return 0, []
    source_order, target_order = occupied.index(source_index), occupied.index(target_index)
    return target_order - source_order, occupied[source_order + 1:target_order]


def _forward_context(nodes: list[dict[str, Any]], links: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], set[str], dict[str, list[str]]]:
    """Index existing links only; it is deliberately not a second topology builder."""
    index = {node["node_id"]: node for node in nodes}
    usable: dict[str, list[dict[str, Any]]] = {node["node_id"]: [] for node in nodes}
    for link in links:
        if link.get("direction") in {"forward", "support"} and link.get("source") in index and link.get("target") in index:
            usable[link["source"]].append(link)
    for rows in usable.values():
        rows.sort(key=lambda item: item["link_id"])
    starts = sorted(node["node_id"] for node in nodes if node.get("vertical_index") in {0, 1})
    reached, paths = set(starts), {node_id: [node_id] for node_id in starts}
    queue = deque(starts)
    while queue:
        source = queue.popleft()
        for link in usable.get(source, []):
            target = link["target"]
            if target not in reached:
                reached.add(target)
                paths[target] = paths[source] + [target]
                queue.append(target)
    return usable, reached, paths


def _events(nodes: list[dict[str, Any]], links: list[dict[str, Any]], occupied: list[int], reached: set[str]) -> list[dict[str, Any]]:
    by_id = {node["node_id"]: node for node in nodes}
    events = []
    for link in links:
        source, target = by_id.get(link.get("source")), by_id.get(link.get("target"))
        if not source or not target or link.get("direction") != "forward":
            continue
        gain, skipped = _gain(source, target, occupied)
        if gain <= 0:
            continue
        events.append({
            "link_id": link["link_id"], "source": source["node_id"], "target": target["node_id"],
            "source_band": source.get("vertical_band"), "target_band": target.get("vertical_band"),
            "source_region": source.get("lateral_slot"), "target_region": target.get("lateral_slot"),
            "occupied_line_gain": gain, "skipped_occupied_lines": skipped,
            "reachable_from_configured_base": source["node_id"] in reached,
        })
    return sorted(events, key=lambda item: item["link_id"])


def _highest(nodes: list[dict[str, Any]], reached: set[str]) -> dict[str, Any] | None:
    candidates = [node for node in nodes if node["node_id"] in reached and isinstance(node.get("vertical_index"), int)]
    if not candidates:
        return None
    maximum = max(node["vertical_index"] for node in candidates)
    rows = sorted((node for node in candidates if node["vertical_index"] == maximum), key=lambda node: node["node_id"])
    return {"vertical_index": maximum, "vertical_band": rows[0].get("vertical_band"), "node_ids": [node["node_id"] for node in rows]}


def _route_profiles(v2: dict[str, Any], qualitative: dict[str, Any] | None, events_by_link: dict[str, dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    families = ((qualitative or {}).get("route_diversity") or {}).get("families") or []
    routes = {route["route_id"]: route for route in v2.get("progression_routes", [])}
    if not families:
        families = [{"family_id": "route:" + route_id, "raw_route_ids": [route_id]} for route_id in sorted(routes)]
    profiles = []
    for family in sorted(families, key=lambda item: item.get("family_id", "")):
        route_ids = sorted(route_id for route_id in family.get("raw_route_ids", []) if route_id in routes)
        if not route_ids:
            continue
        node_ids = routes[route_ids[0]].get("node_ids", [])
        route_events = [events_by_link[f"{source}->{target}"] for source, target in zip(node_ids, node_ids[1:]) if f"{source}->{target}" in events_by_link]
        route_nodes = [by_id[node_id] for node_id in node_ids if node_id in by_id]
        first = route_nodes[0] if route_nodes else {}
        last = route_nodes[-1] if route_nodes else {}
        first_event = route_events[0] if route_events else None
        # Existing forward-only Connectivity routes normally do not encode same-line
        # prefixes.  This records only an explicit existing support link into the
        # first advancing structure; it does not claim that transfer is mandatory.
        lateral_prefixes = [] if not first_event else [link for link in v2.get("structural_links", [])
            if link.get("direction") == "support" and link.get("target") == first_event["source"]
            and by_id.get(link.get("source"), {}).get("lateral_slot") != by_id.get(link.get("target"), {}).get("lateral_slot")]
        profiles.append({
            "route_family_id": family.get("family_id"), "origin_band": first.get("vertical_band"), "destination_band": last.get("vertical_band"),
            "origin_region": first.get("lateral_slot"), "destination_region": last.get("lateral_slot"),
            "advancement_events": route_events, "occupied_line_gains": sum(item["occupied_line_gain"] for item in route_events),
            "line_skips": [item for item in route_events if item["skipped_occupied_lines"]],
            "highest_reachable_line": {"vertical_index": last.get("vertical_index"), "vertical_band": last.get("vertical_band")} if last else None,
            "regions_used": sorted({node.get("lateral_slot") for node in route_nodes if node.get("lateral_slot") in REGIONS}),
            "lateral_transfers_before_advancement": len(lateral_prefixes),
            "reaches_forward_line": last.get("vertical_band") == "forward",
            "reaches_attacking_midfield_line": any(node.get("vertical_band") == "attacking_midfield" for node in route_nodes),
            "advance_then_stall": False, "role_adjustments": [],
            "raw_route_ids": route_ids,
        })
    return profiles


def _regional(nodes: list[dict[str, Any]], reached: set[str], events: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {node["node_id"]: node for node in nodes}
    output = {}
    for region in REGIONS:
        regional_events = [event for event in events if event["source_region"] == region and event["reachable_from_configured_base"]]
        # A region's advancement is anchored at sources in that region.  Its
        # highest line must include their existing targets even when the target
        # is central (for example AML -> ST), otherwise status and highest-line
        # descriptions contradict each other.
        regional_node_ids = ({event["source"] for event in regional_events} | {event["target"] for event in regional_events})
        if not regional_node_ids:
            regional_node_ids = {node["node_id"] for node in nodes if node.get("lateral_slot") == region and node["node_id"] in reached}
        regional_nodes = [by_id[node_id] for node_id in regional_node_ids if node_id in by_id]
        regional_highest = _highest(regional_nodes, regional_node_ids)
        reaches_forward = any(event["target_band"] == "forward" for event in regional_events)
        if reaches_forward: status = "advancement_to_forward"
        elif regional_events: status = "advancement_to_intermediate"
        elif regional_nodes: status = "support_or_lateral_only"
        else: status = "no_structural_advancement"
        output[region] = {"status": status, "advancement_available": bool(regional_events), "highest_reachable_line": regional_highest,
                          "complete_advancement_to_forward_line": reaches_forward, "requires_transfer_from_another_region": None,
                          "contributes_only_support_or_lateral_access": status == "support_or_lateral_only",
                          "advancement_event_ids": [event["link_id"] for event in regional_events],
                          "limitation": "Region describes configured structural links only; it does not estimate use frequency."}
    return output


def _stalls(nodes: list[dict[str, Any]], links: list[dict[str, Any]], events: list[dict[str, Any]], reached: set[str]) -> list[dict[str, Any]]:
    by_id = {node["node_id"]: node for node in nodes}
    outgoing = {node["node_id"]: [] for node in nodes}
    for link in links: outgoing.get(link.get("source"), []).append(link)
    stalled = []
    for event in events:
        target = by_id[event["target"]]
        if not event["reachable_from_configured_base"] or target.get("vertical_band") == "forward":
            continue
        further = any(link.get("direction") == "forward" and by_id.get(link.get("target"), {}).get("vertical_index", -1) > target.get("vertical_index", -1) for link in outgoing[target["node_id"]])
        if not further:
            context = [link.get("direction") for link in outgoing[target["node_id"]]]
            stalled.append({"stalled_at_position": target["node_id"], "stalled_band": target.get("vertical_band"), "origin_region": event["source_region"],
                            "available_support_or_recycle": any(direction in {"support", "backward"} for direction in context),
                            "limitation": "No later existing forward structural link is available from this receiving structure."})
    return sorted(stalled, key=lambda item: item["stalled_at_position"])


def _dependency(nodes: list[dict[str, Any]], links: list[dict[str, Any]], occupied: list[int]) -> list[dict[str, Any]]:
    _, baseline_reached, _ = _forward_context(nodes, links)
    baseline_highest = _highest(nodes, baseline_reached)
    baseline_forward = any(node["node_id"] in baseline_reached and node.get("vertical_band") == "forward" for node in nodes)
    baseline_events = _events(nodes, links, occupied, baseline_reached)
    result = []
    for candidate in sorted(nodes, key=lambda item: item["node_id"]):
        if candidate.get("vertical_index") in {0, 1} or candidate.get("vertical_band") == "forward":
            continue
        reduced_nodes = [node for node in nodes if node["node_id"] != candidate["node_id"]]
        reduced_links = [link for link in links if candidate["node_id"] not in {link.get("source"), link.get("target")}]
        _, reduced_reached, _ = _forward_context(reduced_nodes, reduced_links)
        reduced_highest = _highest(reduced_nodes, reduced_reached)
        reduced_forward = any(node["node_id"] in reduced_reached and node.get("vertical_band") == "forward" for node in reduced_nodes)
        reduced_events = _events(reduced_nodes, reduced_links, occupied, reduced_reached)
        claims = []
        if baseline_forward and not reduced_forward: claims.append("all_forward_line_access_removed")
        if any(event["target_region"] == "centre" for event in baseline_events) and not any(event["target_region"] == "centre" for event in reduced_events): claims.append("all_central_advancement_removed")
        if any(event["occupied_line_gain"] > 1 for event in baseline_events) and not any(event["occupied_line_gain"] > 1 for event in reduced_events): claims.append("all_multi_line_progression_removed")
        if baseline_highest and (not reduced_highest or reduced_highest["vertical_index"] < baseline_highest["vertical_index"]): claims.append("highest_reachable_line_reduced")
        if claims: result.append({"node_id": candidate["node_id"], "proven_claims": claims, "limitation": "Removal simulation uses only frozen structural links; it is not a player substitution prediction."})
    return result


def _role_adjustments(v2: dict[str, Any]) -> list[dict[str, Any]]:
    classes = {"send_forward": "distribution_modifier", "receive_between_lines": "reception_modifier", "receive_centrally": "reception_modifier",
               "advance_to_attacking_midfield": "movement_modifier", "move_into_halfspace": "half_space_modifier", "move_inside": "movement_modifier",
               "attack_space_in_behind": "movement_modifier"}
    rows = []
    for item in v2.get("role_modifiers", []):
        for semantic in item.get("items", []):
            semantic_id = semantic.get("semantic_id")
            if semantic_id in classes:
                rows.append({"node_id": item.get("node_id"), "semantic_id": semantic_id, "classification": classes[semantic_id],
                             "behaviour_id": semantic.get("behaviour_id"), "evidence_ids": sorted(semantic.get("evidence_ids", [])),
                             "limitation": "Role semantics explain potential use of existing structure and do not create topology, gain, or skips."})
    return sorted(rows, key=lambda item: (item["node_id"], item["semantic_id"], item.get("behaviour_id") or ""))


def evaluate_progression(connectivity_v2: dict[str, Any], connectivity_evaluation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return JSON-compatible Phase 1 Progression interpretation of frozen v2 data."""
    v2 = deepcopy(connectivity_v2)
    nodes, links = v2.get("nodes", []), v2.get("structural_links", [])
    lines = _ordered_lines(nodes); occupied = [line["vertical_index"] for line in lines]
    _, reached, _ = _forward_context(nodes, links)
    events = _events(nodes, links, occupied, reached); event_by_link = {event["link_id"]: event for event in events}
    by_id = {node["node_id"]: node for node in nodes}
    profiles = _route_profiles(v2, connectivity_evaluation, event_by_link, by_id)
    stalls = _stalls(nodes, links, events, reached)
    transitions = []
    for source_index, target_index in zip(occupied, occupied[1:]):
        covered = any(event["occupied_line_gain"] == 1 and by_id[event["source"]].get("vertical_index") == source_index and by_id[event["target"]].get("vertical_index") == target_index and event["reachable_from_configured_base"] for event in events)
        transitions.append({"from_vertical_index": source_index, "to_vertical_index": target_index, "status": "advanced" if covered else "not_advanced"})
    if not transitions: continuity = "interrupted"
    elif all(row["status"] == "advanced" for row in transitions): continuity = "continuous"
    elif any(row["status"] == "advanced" for row in transitions): continuity = "partial"
    else: continuity = "interrupted"
    skips = [event for event in events if event["skipped_occupied_lines"]]
    return {"occupied_lines": lines, "advancement_continuity": {"status": continuity, "transitions": transitions,
            "definition": "Continuous means each consecutive occupied tactical line has an existing reachable one-line advancement event."},
            "highest_reachable_line": _highest(nodes, reached), "regional_advancement": _regional(nodes, reached, events),
            "route_profiles": profiles, "line_skips": skips, "advance_then_stall": stalls,
            "progression_dependency": _dependency(nodes, links, occupied), "role_adjustments": _role_adjustments(v2),
            "observations": [{"type": "advancement_events", "count": len(events)}, {"type": "route_profiles", "count": len(profiles)}],
            "limitations": ["Consumes existing Connectivity v2 structural links only; it does not generate links or replace Connectivity routes.",
                            "Advancement is configured occupied-line structure, not an observed pass, quality estimate, score, or prediction.",
                            "Support and recycle are context only and are not counted as advancement.",
                            "Team instructions, player attributes, display coordinates, and match events are unmodelled."]}
