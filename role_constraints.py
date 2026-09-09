"""Role-catalog UI availability checks; independent from role behaviours."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_PATH = Path(__file__).resolve().with_name("role_catalog.json")
REQUIRED_ROLE_FIELDS = {
    "internal_id", "phase", "role_families", "available_starting_positions",
    "available_starting_positions_verification", "role_name_ko", "role_name_en",
    "display_abbr", "display_abbr_verification", "name_verified",
    "role_behaviour_ref", "evidence", "formation_constraints",
}


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(f"Role catalog: {message}")


def load_role_catalog(path: Path = DEFAULT_PATH) -> List[Dict[str, Any]]:
    return validate_role_catalog(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def validate_role_catalog(catalog: Any) -> List[Dict[str, Any]]:
    _require(isinstance(catalog, list), "root must be an array")
    identifiers = set()
    for role in catalog:
        _require(isinstance(role, dict), "role must be an object")
        _require(REQUIRED_ROLE_FIELDS <= role.keys(), "missing role fields")
        _require(isinstance(role["internal_id"], str) and role["internal_id"], "invalid internal_id")
        _require(role["internal_id"] not in identifiers, "duplicate internal_id")
        identifiers.add(role["internal_id"])
        _require(role["phase"] in ("IP", "OOP"), "invalid phase")
        _require(isinstance(role["role_families"], list) and role["role_families"], "role_families must be a non-empty array")
        _require(all(isinstance(family, str) and family for family in role["role_families"]), "invalid role family")
        _require(len(role["role_families"]) == len(set(role["role_families"])), "duplicate role family")
        _require(isinstance(role["available_starting_positions"], list), "positions must be an array")
        _require(all(isinstance(position, str) and position for position in role["available_starting_positions"]), "invalid position")
        _require(role["available_starting_positions_verification"] in ("unknown", "user_ingame_verified"), "invalid position verification")
        _require(isinstance(role["display_abbr"], str) or role["display_abbr"] is None, "invalid display_abbr")
        _require(role["display_abbr_verification"] in ("user_ingame_verified", "provisional_user_filename", "unverified"), "invalid abbr verification")
        reference = role["role_behaviour_ref"]
        _require(reference is None or (isinstance(reference, dict) and reference.get("phase") == role["phase"] and isinstance(reference.get("role"), str)), "invalid behaviour reference")
        _require(isinstance(role["formation_constraints"], list), "constraints must be an array")
        evidence_ids = {item.get("evidence_id") for item in role["evidence"] if isinstance(item, dict)}
        for constraint in role["formation_constraints"]:
            _require(isinstance(constraint, dict), "constraint must be an object")
            _require(constraint.get("constraint_type") == "formation_player_count", "unsupported constraint")
            _require(constraint.get("phase") == role["phase"], "constraint phase mismatch")
            _require(constraint.get("scope") == "centre_back_line", "unsupported constraint scope")
            _require(constraint.get("comparison") == "eq" and constraint.get("value") == 3, "unsupported count constraint")
            _require(constraint.get("verification") == "user_ingame_verified", "unverified constraint")
            _require(set(constraint.get("evidence_ids", [])) <= evidence_ids, "unresolved constraint evidence")
    return copy.deepcopy(catalog)


def resolve_role_knowledge(role: Dict[str, Any], behaviour_kb: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create one read-only role view without duplicating the behaviour KB in the catalog."""
    role = copy.deepcopy(role)
    reference = role.pop("role_behaviour_ref")
    entry = next((item for item in behaviour_kb if reference and item["phase"] == reference["phase"] and item["role"] == reference["role"]), None)
    behaviours = []
    if entry and entry.get("behaviour_verified"):
        behaviours = [
            copy.deepcopy(item) for item in entry["behaviours"]
            if item.get("verification") in ("official", "verified", "user_ingame_verified")
        ]
    role["role_tags"] = [item for item in behaviours if item["category"] == "role_classification"]
    role["described_behaviours"] = [item for item in behaviours if item["category"] != "role_classification"]
    role["player_instructions"] = copy.deepcopy(entry.get("player_instructions", [])) if entry else []
    role["evidence"] = _deduplicate_evidence(role["evidence"] + (entry["evidence"] if entry else []))
    return role


def _deduplicate_evidence(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    output = []
    for item in items:
        evidence_id = item.get("evidence_id")
        if evidence_id not in seen:
            seen.add(evidence_id)
            output.append(copy.deepcopy(item))
    return output


def resolve_catalog(catalog: List[Dict[str, Any]], behaviour_kb: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolve all catalog entries; catalogue and behaviour input objects remain unchanged."""
    return [resolve_role_knowledge(role, behaviour_kb) for role in validate_role_catalog(catalog)]


def role_availability(role: Dict[str, Any], centre_back_line_player_count: int | None) -> Dict[str, Any]:
    """Return a UI availability state only. It never infers a role behaviour."""
    constraints = role["formation_constraints"]
    if not constraints:
        return {"status": "no_verified_restriction", "constraints": []}
    if centre_back_line_player_count is None:
        return {"status": "unknown", "constraints": copy.deepcopy(constraints)}
    active = all(centre_back_line_player_count == constraint["value"] for constraint in constraints)
    return {
        "status": "active" if active else "inactive",
        "constraints": copy.deepcopy(constraints),
    }
