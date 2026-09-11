"""Read-only qualitative interpretation of Connectivity v2 topology.

This module never creates, removes, or reclassifies structural links.  It only
describes the complete graph returned by ``connectivity_engine_v2``.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

_REGIONS = ("left", "centre", "right")
_ROLE_LABELS = {
    "move_inside": "중앙 이동 근거", "move_into_halfspace": "하프스페이스 이동 근거",
    "hold_width": "폭 유지 근거", "receive_between_lines": "라인 사이 수신 근거",
    "receive_centrally": "중앙 수신 근거", "support_central_passing_links": "중앙 패스 연결 보조 근거",
    "open_space_for_fullback": "풀백을 위한 공간 형성 근거", "attack_space_in_behind": "수비 뒤 공간 침투 근거",
    "send_forward": "전방 전달 근거", "send_simple_pass": "간단한 패스 제공 근거",
    "move_to_receive": "공을 받기 위한 이동 근거",
}


def _route_region(route: dict[str, Any], nodes: dict[str, dict[str, Any]], *, last: bool = False) -> str:
    choices = [nodes[node_id].get("lateral_slot") for node_id in route["node_ids"]]
    iterable = reversed(choices) if last else choices
    return next((slot for slot in iterable if slot in {"left", "right"}), "centre")


def _family_rows(nodes: list[dict[str, Any]], routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {node["node_id"]: node for node in nodes}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[str, dict[str, Any]] = {}
    for route in routes:
        path = route["node_ids"]
        slots = [by_id[node_id].get("lateral_slot") for node_id in path]
        origin = _route_region(route, by_id)
        final = _route_region(route, by_id, last=True)
        counts = {region: slots.count(region) for region in _REGIONS}
        dominant = max(_REGIONS, key=lambda region: (counts[region], region == origin, -_REGIONS.index(region)))
        sequence = [by_id[node_id].get("vertical_index") for node_id in path]
        bridges = path[1:-1]
        family_id = "|".join((origin, dominant, final, ",".join(map(str, sequence)), ",".join(bridges)))
        grouped[family_id].append(route)
        metadata[family_id] = {
            "family_id": family_id, "origin_region": origin, "dominant_region": dominant,
            "final_region": final, "occupied_line_sequence": sequence, "major_connectors": bridges,
        }
    rows = []
    for family_id in sorted(grouped):
        members = sorted(grouped[family_id], key=lambda route: route["route_id"])
        representative = min(members, key=lambda route: (len(route["node_ids"]), route["route_id"]))
        rows.append({**metadata[family_id], "representative_route_id": representative["route_id"],
                     "raw_route_ids": [route["route_id"] for route in members]})
    return rows


def _routes_from_graph(nodes: list[dict[str, Any]], links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    forward: dict[str, list[str]] = defaultdict(list)
    for link in links:
        if link.get("direction") == "forward": forward[link["source"]].append(link["target"])
    by_id = {node["node_id"]: node for node in nodes}
    starts = [node["node_id"] for node in nodes if node.get("vertical_index") in (0, 1)]
    ends = {node["node_id"] for node in nodes if node.get("vertical_band") == "forward"}
    found: list[dict[str, Any]] = []
    def walk(path: list[str]) -> None:
        current = path[-1]
        if current in ends and len(path) > 1:
            found.append({"route_id": "->".join(path), "node_ids": path}); return
        if len(path) >= 6: return
        for target in sorted(forward.get(current, [])):
            if target not in path: walk(path + [target])
    for start in sorted(starts): walk([start])
    unique: dict[str, dict[str, Any]] = {route["route_id"]: route for route in found}
    return [unique[key] for key in sorted(unique)]


def _line_continuity(nodes: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    occupied = sorted({node["vertical_index"] for node in nodes if isinstance(node.get("vertical_index"), int)})
    transitions = []
    for source, target in zip(occupied, occupied[1:]):
        covered = any(link.get("direction") == "forward" and
                      next(node for node in nodes if node["node_id"] == link["source"])["vertical_index"] == source and
                      next(node for node in nodes if node["node_id"] == link["target"])["vertical_index"] == target
                      for link in links)
        transitions.append({"from_vertical_index": source, "to_vertical_index": target, "status": "covered" if covered else "not_covered"})
    covered_count = sum(item["status"] == "covered" for item in transitions)
    status = "continuous" if transitions and covered_count == len(transitions) else "partial" if covered_count else "interrupted"
    return {"status": status, "occupied_vertical_indexes": occupied, "transitions": transitions,
            "limitations": ["Configured occupied lines are evaluated; named FM tactical bands are not required."]}


def _reachable_path(nodes: list[dict[str, Any]], links: list[dict[str, Any]], source_region: str, target_region: str, *, via_centre: bool = False) -> list[str] | None:
    by_id = {node["node_id"]: node for node in nodes}; adjacency: dict[str, list[str]] = defaultdict(list)
    for link in links: adjacency[link["source"]].append(link["target"])
    queue = deque((node["node_id"], [node["node_id"]]) for node in nodes if node.get("lateral_slot") == source_region)
    visited = {node_id for node_id, _ in queue}
    while queue:
        current, path = queue.popleft()
        if by_id[current].get("lateral_slot") == target_region and len(path) > 1 and (not via_centre or any(by_id[item].get("lateral_slot") == "centre" for item in path)):
            return path
        for target in sorted(adjacency.get(current, [])):
            if target not in visited: visited.add(target); queue.append((target, path + [target]))
    return None


def _support_recycle(nodes: list[dict[str, Any]], links: list[dict[str, Any]], routes: list[dict[str, Any]]) -> dict[str, Any]:
    terminals = {route["node_ids"][-1] for route in routes}
    participants = sorted({node_id for route in routes for node_id in route["node_ids"][:-1]} - terminals)
    rows = []
    for node_id in participants:
        outgoing = [link for link in links if link["source"] == node_id]
        backward = any(link.get("direction") == "backward" for link in outgoing)
        support = any(link.get("direction") == "support" for link in outgoing)
        status = "multiple_fallback_types" if backward and support else "one_fallback_type" if backward or support else "fallback_not_detected"
        rows.append({"node_id": node_id, "status": status, "backward_outlet": backward, "same_line_support": support})
    return {"nodes": rows, "limitations": ["Fallback structure does not estimate retention, decision-making, or pass success."]}


def _dependency(nodes: list[dict[str, Any]], links: list[dict[str, Any]], routes: list[dict[str, Any]], families: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_by_region = {region: {row["family_id"] for row in families if row["dominant_region"] == region} for region in _REGIONS}
    eligible = sorted({node_id for route in routes for node_id in route["node_ids"][1:-1]})
    rows: list[dict[str, Any]] = []; bottlenecks: list[dict[str, Any]] = []
    for node_id in eligible:
        surviving_nodes = [node for node in nodes if node["node_id"] != node_id]
        surviving_links = [link for link in links if link["source"] != node_id and link["target"] != node_id]
        survivors = _family_rows(surviving_nodes, _routes_from_graph(surviving_nodes, surviving_links))
        survivor_by_region = {region: {row["family_id"] for row in survivors if row["dominant_region"] == region} for region in _REGIONS}
        affected = [region for region in _REGIONS if baseline_by_region[region] and not survivor_by_region[region]]
        any_survivor = any(survivor_by_region[region] for region in _REGIONS)
        lost_family = any(baseline_by_region[region] - survivor_by_region[region] for region in _REGIONS)
        if not any_survivor: impact = "all_complete_progression_removed"
        elif affected: impact = "regional_progression_removed"
        elif lost_family: impact = "removes_one_alternative"
        else: impact = "no_meaningful_impact"
        row = {"node_id": node_id, "impact": impact, "affected_regions": affected,
               "classification": "critical_structural_bridge" if impact == "all_complete_progression_removed" else "regional_structural_bridge" if impact == "regional_progression_removed" else None,
               "limitations": ["Node removal tests configured topology only; it does not model substitutions or match behaviour."]}
        rows.append(row)
        if row["classification"]: bottlenecks.append(row)
    return rows, bottlenecks


def _dead_ends_and_isolation(nodes: list[dict[str, Any]], links: list[dict[str, Any]], routes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    incident = defaultdict(list)
    for link in links: incident[link["source"]].append(link); incident[link["target"]].append(link)
    isolated = [{"node_id": node["node_id"], "status": "isolated_configured_node", "configured_position": node.get("configured_position")}
                for node in nodes if not incident[node["node_id"]]]
    forward = defaultdict(list)
    for link in links:
        if link.get("direction") == "forward": forward[link["source"]].append(link["target"])
    starts = {node["node_id"] for node in nodes if node.get("vertical_index") in (0, 1)}
    reached = set(starts); queue = deque(starts)
    while queue:
        node_id = queue.popleft()
        for target in forward[node_id]:
            if target not in reached: reached.add(target); queue.append(target)
    on_complete = {node_id for route in routes for node_id in route["node_ids"]}
    dead = []
    for node in nodes:
        node_id = node["node_id"]
        # Safe rule: only a central, non-forward, reached relay candidate may be reported.
        if node_id not in reached or node_id in on_complete or node.get("vertical_band") == "forward" or node.get("lateral_slot") != "centre": continue
        outgoing = [link for link in links if link["source"] == node_id]
        if not any(link.get("direction") in {"forward", "backward", "support"} for link in outgoing):
            dead.append({"node_id": node_id, "status": "structural_dead_end_candidate", "configured_position": node.get("configured_position"),
                         "limitations": ["Wide nodes and configured forward endpoints are deliberately excluded from this safe candidate rule."]})
    return dead, isolated


def _role_adjustments(v2: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for group in v2.get("role_modifiers", []):
        for item in group.get("items", []):
            label = _ROLE_LABELS.get(item.get("semantic_id"))
            if label:
                rows.append({"node_id": group["node_id"], "interpretation": label,
                             "evidence_ids": sorted(item.get("evidence_ids", [])),
                             "limitation": "Role behaviour is an interpretation modifier and does not alter baseline structural links."})
    return sorted(rows, key=lambda row: (row["node_id"], row["interpretation"], row["evidence_ids"]))


def evaluate_connectivity_v2(v2: dict[str, Any]) -> dict[str, Any]:
    """Return JSON-compatible qualitative output without mutating *v2*."""
    nodes = v2.get("nodes", []); links = v2.get("structural_links", []); routes = v2.get("progression_routes", [])
    continuity = _line_continuity(nodes, links)
    families = _family_rows(nodes, routes)
    regional = {}
    for region in _REGIONS:
        rows = [row for row in families if row["dominant_region"] == region]
        shared = sorted(set.intersection(*(set(row["major_connectors"]) for row in rows))) if len(rows) > 1 else []
        status = "multiple_structurally_distinct_route_families" if len(rows) > 1 else "complete_route_present" if rows else "no_complete_regional_route_detected"
        regional[region] = {"status": status, "route_family_ids": [row["family_id"] for row in rows], "shared_connector_ids": shared,
                            "limitations": ["A shared connector is not dependency without node-removal survival evidence."]}
    cross = {}
    for source, target, key, via in (("left", "centre", "left_to_centre", False), ("centre", "left", "centre_to_left", False), ("centre", "right", "centre_to_right", False), ("right", "centre", "right_to_centre", False), ("left", "right", "left_to_right_via_centre", True), ("right", "left", "right_to_left_via_centre", True)):
        path = _reachable_path(nodes, links, source, target, via_centre=via)
        cross[key] = {"status": "access_detected" if path else "access_not_detected", "path_node_ids": path or [],
                      "limitations": ["Access is a configured structural path, not an observed ball circulation."]}
    support = _support_recycle(nodes, links, routes)
    dependency, bottlenecks = _dependency(nodes, links, routes, families)
    dead, isolated = _dead_ends_and_isolation(nodes, links, routes)
    observations = []
    if continuity["status"] == "continuous": observations.append("점유 라인이 순서대로 구조적으로 이어집니다.")
    elif continuity["status"] == "partial": observations.append("일부 인접 점유 라인 사이의 구조적 전진 연결이 확인되지 않습니다.")
    else: observations.append("깊은 구조에서 전방까지의 완결 전진 경로가 현재 확인되지 않습니다.")
    for region in _REGIONS:
        if regional[region]["status"] != "no_complete_regional_route_detected": observations.append({"left":"왼쪽", "centre":"중앙", "right":"오른쪽"}[region] + "을 통한 완결 전진 경로가 있습니다.")
    if any(item["impact"] == "regional_progression_removed" for item in dependency): observations.append("일부 전진 경로는 특정 연결점 제거 시 해당 지역의 완결 경로를 잃습니다.")
    if any(item["impact"] == "all_complete_progression_removed" for item in dependency): observations.append("특정 연결점 제거 시 현재 구성된 모든 완결 전진 경로가 사라집니다.")
    if any(item["status"] == "fallback_not_detected" for item in support["nodes"]): observations.append("일부 전진 참여 위치에서 되돌림 또는 같은 라인 지원 구조가 확인되지 않습니다.")
    return {
        "line_continuity": continuity,
        "progression": {"status": "complete_route_present" if routes else "no_complete_route_detected", "route_family_ids": [row["family_id"] for row in families], "limitations": ["Raw route count is debug data and is not a quality judgement."]},
        "route_diversity": {"families": families, "limitations": ["Families deduplicate routes with the same topology signature."]},
        "regional_connectivity": regional, "cross_region_access": cross, "support_recycle": support,
        "connector_dependency": dependency, "structural_bottlenecks": bottlenecks, "dead_ends": dead, "isolated_nodes": isolated,
        "role_adjustments": _role_adjustments(v2), "observations": observations,
        "debug": {"raw_route_count": len(routes), "distinct_route_family_count": len(families)},
        "limitations": ["Evaluation consumes the full structural topology, not display-priority links.", "No score, formation ranking, pass success, player ability, opponent pressure, or team-instruction effect is inferred.", "Role evidence is modifier-only; missing evidence does not reduce baseline structure."],
    }
