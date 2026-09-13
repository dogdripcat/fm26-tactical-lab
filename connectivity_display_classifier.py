"""Deterministic, presentation-only connectivity states."""
from __future__ import annotations


def classify_links(connectivity_v2, support_evaluation=None, relevant_candidates=()):
    """Classify existing links without creating or changing Connectivity topology.

    An ``unsupported`` row can only come from an explicitly supplied, tactically
    relevant candidate. Callers must never manufacture all player-pair rows.
    """
    support = {row.get("receiver_id"): row for row in (support_evaluation or {}).get("receiving_states", [])}
    route_links = {f"{nodes[index]}->{nodes[index + 1]}" for route in connectivity_v2.get("progression_routes", []) for nodes in [route.get("node_ids", [])] for index in range(max(0, len(nodes) - 1))}
    rows = []
    for link in connectivity_v2.get("structural_links", []):
        receiver = support.get(link.get("target"), {})
        directions = receiver.get("support_directions", [])
        if link.get("direction") == "forward" and link.get("link_id") in route_links and len(directions) > 1:
            state, reasons = "very_strong", ["forward_route", "multiple_post_reception_directions"]
        elif receiver.get("support_isolated") or receiver.get("single_option_support"):
            state, reasons = "weak", ["limited_post_reception_support"]
        else:
            state, reasons = "smooth", ["existing_structural_relationship"]
        rows.append({"link_id": link.get("link_id"), "source": link.get("source"), "target": link.get("target"), "state": state, "reasons": reasons, "is_structural_link": True})
    existing = {row["link_id"] for row in rows}
    for candidate in relevant_candidates:
        candidate_id = candidate.get("link_id")
        if not candidate_id or candidate_id in existing or candidate.get("status") != "structurally_unsupported":
            continue
        rows.append({"link_id": candidate_id, "source": candidate.get("source"), "target": candidate.get("target"), "state": "unsupported", "reasons": ["explicit_relevant_candidate_unsupported"], "is_structural_link": False})
    return rows
