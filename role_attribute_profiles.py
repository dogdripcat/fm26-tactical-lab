"""Verified role key-attribute profiles; never player requirements or thresholds."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import role_constraints


DEFAULT_PATH = Path(__file__).resolve().with_name("role_attribute_profiles.json")
ATTRIBUTE_VERIFICATIONS = {"user_ingame_verified", "official_verified"}
FORBIDDEN_VALUE_FIELDS = {"value", "minimum", "maximum", "threshold", "recommended_value"}


def load_role_attribute_profiles(path: Path = DEFAULT_PATH) -> dict[str, Any]:
    """Load a JSON-compatible, evidence-backed registry without mutating it."""
    return validate_role_attribute_profiles(
        json.loads(Path(path).read_text(encoding="utf-8-sig")),
        role_constraints.load_role_catalog(),
    )


def validate_role_attribute_profiles(data: Any, catalog: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("profiles"), list):
        raise ValueError("role attribute profiles must contain a profiles array")
    catalog_by_id = {role["internal_id"]: role for role in role_constraints.validate_role_catalog(catalog)}
    seen_profiles = set()
    for profile in data["profiles"]:
        if not isinstance(profile, dict):
            raise ValueError("role attribute profile must be an object")
        required = {"profile_id", "role_internal_id", "phase", "position_family", "role_name_ko", "key_attributes", "evidence"}
        if not required <= profile.keys() or profile.keys() & FORBIDDEN_VALUE_FIELDS:
            raise ValueError("invalid role attribute profile fields")
        profile_id = profile["profile_id"]
        if not isinstance(profile_id, str) or not profile_id or profile_id in seen_profiles:
            raise ValueError("duplicate or invalid profile_id")
        seen_profiles.add(profile_id)
        role = catalog_by_id.get(profile["role_internal_id"])
        if role is None or profile["phase"] != role["phase"]:
            raise ValueError("profile role identity or phase is unresolved")
        if profile["role_name_ko"] != role["role_name_ko"]:
            raise ValueError("profile role label does not match catalog")
        if profile["position_family"] not in role["role_families"]:
            raise ValueError("profile position family does not match catalog")
        evidence = profile["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("profile must have evidence")
        evidence_ids = {item.get("evidence_id") for item in evidence if isinstance(item, dict)}
        if len(evidence_ids) != len(evidence) or not all(isinstance(item.get("evidence_id"), str) and item["evidence_id"] for item in evidence):
            raise ValueError("profile evidence IDs must be unique and non-empty")
        seen_attributes = set()
        for attribute in profile["key_attributes"]:
            if not isinstance(attribute, dict) or attribute.keys() & FORBIDDEN_VALUE_FIELDS:
                raise ValueError("role key attribute must not contain a player value or threshold")
            required_attribute = {"attribute_id", "name_ko", "evidence_ids", "verification"}
            if not required_attribute <= attribute.keys():
                raise ValueError("role key attribute fields are incomplete")
            if not isinstance(attribute["attribute_id"], str) or not attribute["attribute_id"] or attribute["attribute_id"] in seen_attributes:
                raise ValueError("role key attribute IDs must be unique")
            seen_attributes.add(attribute["attribute_id"])
            if not isinstance(attribute["name_ko"], str) or not attribute["name_ko"]:
                raise ValueError("role key attribute Korean label is required")
            if attribute["verification"] not in ATTRIBUTE_VERIFICATIONS:
                raise ValueError("role key attribute verification is invalid")
            if not isinstance(attribute["evidence_ids"], list) or not attribute["evidence_ids"] or not set(attribute["evidence_ids"]) <= evidence_ids:
                raise ValueError("role key attribute evidence is unresolved")
        if not isinstance(profile.get("unresolved_attributes", []), list):
            raise ValueError("unresolved_attributes must be a list")
    return copy.deepcopy(data)


def profile_for_role(role_internal_id: str, phase: str | None = None,
                     profiles: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return a copied profile only for the exact role identity and phase."""
    registry = profiles if profiles is not None else load_role_attribute_profiles()
    for profile in registry["profiles"]:
        if profile["role_internal_id"] == role_internal_id and (phase is None or profile["phase"] == phase):
            return copy.deepcopy(profile)
    return None


def player_attribute_display(profile: dict[str, Any], player_attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prepare a display-only row set from supplied player data; never invent values or fit scores."""
    provided = player_attributes if isinstance(player_attributes, dict) else {}
    rows = []
    for attribute in profile.get("key_attributes", []):
        value = provided.get(attribute["attribute_id"])
        rows.append({"attribute_id": attribute["attribute_id"], "name_ko": attribute["name_ko"],
                     "player_value": value if isinstance(value, (int, float)) else None})
    return {"role_internal_id": profile.get("role_internal_id"), "player_data_available": bool(provided),
            "attributes": rows, "fit_score": None, "recommendation": None}
