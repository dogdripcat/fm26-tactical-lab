"""Pure team-instruction catalogue validation and normalization.

The catalogue is supplied by an adapter.  This module never assigns tactical
effects: it only accepts verified UI identities and preserves missing input.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List


EFFECT_NOT_MODELLED = "effect_not_modelled"


def validate_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("instructions"), list):
        raise ValueError("Team instruction catalogue must contain instructions")
    seen_categories, seen_values = set(), set()
    for item in catalog["instructions"]:
        required = ("internal_id", "phase", "display_name_ko", "identity_verification",
                    "selectable_values", "analysis_status", "evidence_ids", "limitations")
        if not isinstance(item, dict) or any(key not in item for key in required):
            raise ValueError("Invalid team instruction category")
        if item["phase"] not in ("IP", "OOP") or item["internal_id"] in seen_categories:
            raise ValueError("Duplicate or invalid team instruction category")
        seen_categories.add(item["internal_id"])
        if item["analysis_status"] != EFFECT_NOT_MODELLED:
            raise ValueError("Team instruction effects must not be modelled")
        for value in item["selectable_values"]:
            if not isinstance(value, dict) or {"internal_id", "display_name_ko", "verification", "evidence_ids", "analysis_status"} - set(value):
                raise ValueError("Invalid team instruction value")
            if value["internal_id"] in seen_values or value["analysis_status"] != EFFECT_NOT_MODELLED:
                raise ValueError("Duplicate value or modelled team instruction effect")
            seen_values.add(value["internal_id"])
    return copy.deepcopy(catalog)


def normalize_team_instructions(raw: Any, phase: str, catalog: Dict[str, Any]) -> tuple[Dict[str, str], List[Dict[str, str]]]:
    """Return canonical category/value IDs, rejecting unknown or cross-phase input."""
    if raw is None:
        return {}, []
    if not isinstance(raw, dict):
        raise ValueError(f"{phase.lower()}_team_instructions must be an object")
    validated = validate_catalog(catalog)
    by_category = {row["internal_id"]: row for row in validated["instructions"]}
    normalized: Dict[str, str] = {}
    changes: List[Dict[str, str]] = []
    for category_id, value_id in raw.items():
        category = by_category.get(category_id)
        if category is None:
            raise ValueError(f"Unknown team instruction category: {category_id}")
        if category["phase"] != phase:
            raise ValueError(f"Team instruction phase mismatch: {category_id}")
        value = next((row for row in category["selectable_values"] if row["internal_id"] == value_id), None)
        if value is None:
            raise ValueError(f"Unknown team instruction value: {value_id}")
        if value["verification"] != "user_ingame_verified":
            raise ValueError(f"Unverified team instruction value: {value_id}")
        normalized[category_id] = value_id
    return normalized, changes


def input_status(normalized: Dict[str, Any], catalog: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-ready disclosure with no tactical interpretation."""
    return {
        "status": EFFECT_NOT_MODELLED,
        "ip": copy.deepcopy(normalized.get("ip_team_instructions", {})),
        "oop": copy.deepcopy(normalized.get("oop_team_instructions", {})),
        "limitation": "Team instruction tactical effects are not yet modelled.",
    }
