"""Pure configured-position registry and deterministic relation layer.

This module describes starting-position geometry only.  It neither reads role
behaviours nor determines connectivity, pass availability, or edge status.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List


_ROOT = Path(__file__).resolve().parent
_REGISTRY_PATH = _ROOT / "configured_position_registry.json"
_PHASES = frozenset(("IP", "OOP"))
_LATERAL_ORDER = {"left": 0, "centre": 1, "right": 2}
_RELATION_ORDER = (
    "same_lateral_slot", "adjacent_lateral_slot",
    "centre_to_wide", "wide_to_centre",
    "same_vertical_band", "one_band_forward", "multiple_bands_forward",
    "one_band_backward", "multiple_bands_backward",
    "forward_diagonal", "backward_diagonal",
)


def load_configured_position_registry(path: str | Path | None = None) -> Dict[str, Any]:
    """Load and validate the pure-data configured-position registry."""
    source = _REGISTRY_PATH if path is None else Path(path)
    return validate_configured_position_registry(json.loads(source.read_text(encoding="utf-8")))


def validate_configured_position_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(registry, dict) or not isinstance(registry.get("positions"), list):
        raise ValueError("Configured position registry requires a positions array")
    bands = registry.get("vertical_bands")
    if not isinstance(bands, list) or not bands:
        raise ValueError("Configured position registry requires vertical_bands")
    band_indices = {item.get("name"): item.get("index") for item in bands if isinstance(item, dict)}
    if len(band_indices) != len(bands) or len(set(band_indices.values())) != len(bands):
        raise ValueError("Vertical band names and indexes must be unique")
    seen = set()
    for item in registry["positions"]:
        required = {"position_id", "position_family", "vertical_band", "vertical_index", "lateral_slot", "phase_agnostic"}
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError("Configured position entry is incomplete")
        position_id = item["position_id"]
        if not isinstance(position_id, str) or position_id in seen:
            raise ValueError("Configured position IDs must be unique")
        seen.add(position_id)
        if item["lateral_slot"] not in {"left", "centre", "right", "unknown"}:
            raise ValueError("Configured position lateral_slot is invalid")
        if band_indices.get(item["vertical_band"]) != item["vertical_index"]:
            raise ValueError("Configured position vertical band/index mismatch")
        if item["phase_agnostic"] is not True:
            raise ValueError("Configured position registry entries must be phase agnostic")
    canonical_ids = registry.get("canonical_position_ids", [])
    if not isinstance(canonical_ids, list) or not canonical_ids or len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("Configured position registry requires unique canonical_position_ids")
    if not set(canonical_ids) <= seen:
        raise ValueError("Canonical configured position ID is not registered")
    aliases = registry.get("legacy_input_aliases", [])
    if not isinstance(aliases, list):
        raise ValueError("Configured position legacy_input_aliases must be an array")
    alias_names = set()
    for alias in aliases:
        if not isinstance(alias, dict) or not {"raw_position", "canonical_position_id", "status", "basis"} <= alias.keys():
            raise ValueError("Configured position alias is incomplete")
        raw = alias["raw_position"]
        if not isinstance(raw, str) or not raw or raw in alias_names:
            raise ValueError("Configured position alias must be unique")
        alias_names.add(raw)
        if alias["status"] not in {"resolved", "unresolved"}:
            raise ValueError("Configured position alias status is invalid")
        target = alias["canonical_position_id"]
        if alias["status"] == "resolved" and target not in canonical_ids:
            raise ValueError("Resolved configured position alias has invalid canonical target")
        if alias["status"] == "unresolved" and target is not None:
            raise ValueError("Unresolved configured position alias cannot have a canonical target")
    return copy.deepcopy(registry)


def _position_index(registry: Dict[str, Any] | None = None) -> Dict[str, Dict[str, Any]]:
    data = load_configured_position_registry() if registry is None else validate_configured_position_registry(registry)
    return {item["position_id"]: item for item in data["positions"]}


def normalize_configured_position(raw_position: str, registry: Dict[str, Any] | None = None) -> str | None:
    """Resolve only an explicit legacy input alias; unresolved values fail closed."""
    data = load_configured_position_registry() if registry is None else validate_configured_position_registry(registry)
    if not isinstance(raw_position, str):
        return None
    canonical = set(data["canonical_position_ids"])
    if raw_position in canonical:
        return raw_position
    alias = next((row for row in data["legacy_input_aliases"] if row["raw_position"] == raw_position), None)
    if alias and alias["status"] == "resolved":
        return alias["canonical_position_id"]
    return None


def configured_position_alias_status(raw_position: str, registry: Dict[str, Any] | None = None) -> str | None:
    """Return explicit alias status, or None when the input is not an alias record."""
    data = load_configured_position_registry() if registry is None else validate_configured_position_registry(registry)
    if not isinstance(raw_position, str):
        return None
    alias = next((row for row in data["legacy_input_aliases"] if row["raw_position"] == raw_position), None)
    return alias["status"] if alias else None


def build_position_node(phase: str, configured_position: str, role_internal_id: str | None = None,
                        registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return a position-only node; unknown positions deliberately carry no geometry."""
    if phase not in _PHASES:
        raise ValueError("phase must be IP or OOP")
    raw_position = configured_position if isinstance(configured_position, str) else str(configured_position)
    position_id = normalize_configured_position(raw_position, registry) or raw_position
    definition = None if configured_position_alias_status(raw_position, registry) == "unresolved" else _position_index(registry).get(position_id)
    base = {
        "node_id": f"{phase}:{position_id}", "phase": phase,
        "configured_position": position_id, "role_internal_id": role_internal_id,
        "expected_role_space": {"status": "unknown", "items": []},
    }
    if definition is None:
        return {**base, "position_family": "unknown", "vertical_band": "unknown",
                "vertical_index": None, "lateral_slot": "unknown"}
    return {**base, **{key: definition[key] for key in (
        "position_family", "vertical_band", "vertical_index", "lateral_slot",
    )}}


def _basis(node: Dict[str, Any]) -> Dict[str, Any]:
    return {key: node.get(key) for key in (
        "configured_position", "position_family", "vertical_band", "vertical_index", "lateral_slot",
    )}


def calculate_configured_position_relation(source_node: Dict[str, Any], target_node: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate stable configured-position relations without compatibility judgement."""
    source_phase, target_phase = source_node.get("phase"), target_node.get("phase")
    output = {
        "source_node_id": source_node.get("node_id"), "target_node_id": target_node.get("node_id"),
        "phase": source_phase if source_phase == target_phase else None,
        "configured_position_relation": {
            "status": "unknown", "relations": [],
            "basis": {"source": _basis(source_node), "target": _basis(target_node)},
        },
        "expected_role_space_relation": {"status": "unknown", "relations": [], "evidence_ids": []},
        "positional_compatibility": {"status": "unknown", "basis": []},
        "limitations": ["Configured position relations do not establish pass availability or connectivity."],
    }
    if source_phase not in _PHASES or target_phase not in _PHASES or source_phase != target_phase:
        output["configured_position_relation"]["status"] = "invalid_phase"
        output["limitations"].append("Configured position relations are not generated across phases.")
        return output
    source_index, target_index = source_node.get("vertical_index"), target_node.get("vertical_index")
    if not isinstance(source_index, int) or not isinstance(target_index, int):
        output["limitations"].append("One or both configured positions are unknown; no relation is inferred.")
        return output
    relations: List[str] = []
    source_lateral, target_lateral = source_node.get("lateral_slot"), target_node.get("lateral_slot")
    laterals_known = source_lateral in _LATERAL_ORDER and target_lateral in _LATERAL_ORDER
    if laterals_known:
        lateral_delta = _LATERAL_ORDER[target_lateral] - _LATERAL_ORDER[source_lateral]
        if lateral_delta == 0:
            relations.append("same_lateral_slot")
        elif abs(lateral_delta) == 1:
            relations.append("adjacent_lateral_slot")
        if source_lateral == "centre" and target_lateral in {"left", "right"}:
            relations.append("centre_to_wide")
        elif source_lateral in {"left", "right"} and target_lateral == "centre":
            relations.append("wide_to_centre")
    vertical_delta = target_index - source_index
    if vertical_delta == 0:
        relations.append("same_vertical_band")
    elif vertical_delta == 1:
        relations.append("one_band_forward")
    elif vertical_delta > 1:
        relations.append("multiple_bands_forward")
    elif vertical_delta == -1:
        relations.append("one_band_backward")
    else:
        relations.append("multiple_bands_backward")
    if laterals_known and source_lateral != target_lateral:
        if vertical_delta > 0:
            relations.append("forward_diagonal")
        elif vertical_delta < 0:
            relations.append("backward_diagonal")
    output["configured_position_relation"] = {
        "status": "known", "relations": [item for item in _RELATION_ORDER if item in relations],
        "basis": {"source": _basis(source_node), "target": _basis(target_node)},
    }
    return output
