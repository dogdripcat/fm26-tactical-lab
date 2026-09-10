"""Thin Web MVP adapter.  It consumes the existing catalog and core pipeline."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from core.pipeline import analyze_tactic_data
from fm26lab import ROLE_ALIASES, ROLE_DICTIONARY
from current_tactic_evidence_sufficiency import build_current_tactic_evidence_sufficiency
import role_behaviours
import role_constraints
import role_knowledge_coverage
import positional_relationships
from web.pitch_layout import payload as pitch_layout_payload
from web.analysis_presenter import present as present_analysis
from core.team_instructions import validate_catalog


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "sample_leicester_4231.json"
POSITION_REGISTRY_PATH = ROOT / "configured_position_registry.json"
TEAM_INSTRUCTION_CATALOG_PATH = ROOT / "data" / "team_instruction_catalog.json"
LEICESTER_TEAM_INSTRUCTIONS_PATH = ROOT / "data" / "sample_team_instructions_leicester.json"
# Contexts use catalog available_starting_positions as the source of truth.
# Configured-position family and role family deliberately are not forced into 1:1 pairs.
POSITION_CONTEXTS = {
    "GK": (("Goalkeeper",), ()),
    "LB": (("Full-Back",), ()), "RB": (("Full-Back",), ()),
    "wing_back_left": (("Wing-Back",), ()), "wing_back_right": (("Wing-Back",), ()),
    "LCB": (("D(C)",), ()), "CB": (("D(C)",), ()), "DC": (("D(C)",), ()), "RCB": (("D(C)",), ()),
    "DML": (("DM",), ()), "DM": (("DM",), ()), "DMR": (("DM",), ()),
    "MCL": (("CM",), ()), "MC": (("CM",), ()), "MCR": (("CM",), ()),
    "ML": (("Wide Midfield",), ()), "MR": (("Wide Midfield",), ()),
    "AML": (("Winger",), ()), "AMC": (("AM",), ()), "AMR": (("Winger",), ()),
    "ST": (("FW",), ()), "CF": (("FW",), ()),
}

# Presets are configured-position arrays only. They carry no role selection or analysis rule.
FORMATION_PRESETS = {
    "4-2-3-1": ["GK", "LB", "LCB", "RCB", "RB", "DML", "DMR", "AML", "AMC", "AMR", "ST"],
    "4-3-3": ["GK", "LB", "LCB", "RCB", "RB", "DM", "MCL", "MCR", "AML", "AMR", "ST"],
    "4-4-2": ["GK", "LB", "LCB", "RCB", "RB", "ML", "MCL", "MCR", "MR", "ST", "CF"],
    "4-2-4": ["GK", "LB", "LCB", "RCB", "RB", "MCL", "MCR", "AML", "AMR", "ST", "CF"],
    "3-4-2-1": ["GK", "LCB", "DC", "RCB", "wing_back_left", "wing_back_right", "MCL", "MCR", "AML", "AMC", "ST"],
    "3-4-3": ["GK", "LCB", "DC", "RCB", "wing_back_left", "wing_back_right", "MCL", "MCR", "AML", "AMR", "ST"],
    "3-5-2": ["GK", "LCB", "DC", "RCB", "wing_back_left", "wing_back_right", "MCL", "MC", "MCR", "ST", "CF"],
}


def formation_presets_payload() -> Dict[str, Any]:
    """Return only registry-backed configured-position templates for the web UI."""
    registry = json.loads(POSITION_REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    valid_ids = {item["position_id"] for item in registry.get("positions", [])}
    invalid = {
        name: [position for position in positions if position not in valid_ids]
        for name, positions in FORMATION_PRESETS.items()
        if len(positions) != 11 or len(set(positions)) != 11 or any(position not in valid_ids for position in positions)
    }
    if invalid:
        raise ValueError("configured-position preset validation failed")
    return {"phase": "IP", "presets": copy.deepcopy(FORMATION_PRESETS)}


def pitch_layout_payload_for_presets() -> Dict[str, Any]:
    """Web display geometry only; never a tactical relationship input."""
    return pitch_layout_payload(FORMATION_PRESETS)


def centre_back_line_count(positions: list[str]) -> int:
    """Count registered centre-back configured positions; no role inference is involved."""
    registry = json.loads(POSITION_REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    by_id = {item["position_id"]: item for item in registry.get("positions", [])}
    return sum(
        by_id.get(positional_relationships.normalize_configured_position(position) or position, {}).get("position_family") == "centre_back"
        for position in positions
    )


def sample_tactic() -> Dict[str, Any]:
    tactic = json.loads(SAMPLE_PATH.read_text(encoding="utf-8-sig"))
    for key in ("ip_roles", "oop_roles"):
        roles = tactic.get(key)
        if not isinstance(roles, dict):
            continue
        normalized = {}
        for position, role in roles.items():
            canonical = positional_relationships.normalize_configured_position(position) or position
            if canonical in normalized:
                # A collision is deliberately left as the original key; no slot is guessed.
                canonical = position
            normalized[canonical] = role
        tactic[key] = normalized
    return tactic


def team_instructions_payload(phase: str | None = None) -> Dict[str, Any]:
    if phase is not None and phase not in ("IP", "OOP"):
        raise ValueError("phase must be IP or OOP")
    catalog = validate_catalog(json.loads(TEAM_INSTRUCTION_CATALOG_PATH.read_text(encoding="utf-8-sig")))
    grouped = {key: [copy.deepcopy(row) for row in catalog["instructions"] if row["phase"] == key] for key in ("IP", "OOP")}
    return {phase: grouped[phase]} if phase else grouped


def sample_team_instructions_payload() -> Dict[str, Any]:
    """Separate web fixture: it does not mutate the historical golden sample."""
    return copy.deepcopy(json.loads(LEICESTER_TEAM_INSTRUCTIONS_PATH.read_text(encoding="utf-8-sig")))


def _public_role(role: Dict[str, Any], centre_back_line_count: int | None, coverage_by_id: Dict[str, str]) -> Dict[str, Any]:
    availability = role_constraints.role_availability(role, centre_back_line_count)
    verified_abbr = role["display_abbr"] if role["display_abbr_verification"] == "user_ingame_verified" else None
    analysis_token = verified_abbr or role["internal_id"]
    legacy_tokens = [token for (phase, token), canonical in ROLE_ALIASES.items()
                     if phase == role["phase"] and canonical == verified_abbr]
    identity_status = "unresolved" if role.get("ambiguity", {}).get("status") == "unresolved" else "verified"
    return {
        "role_internal_id": role["internal_id"], "phase": role["phase"],
        "role_name_ko": role["role_name_ko"], "role_families": copy.deepcopy(role["role_families"]),
        "available_starting_positions": copy.deepcopy(role["available_starting_positions"]),
        "abbreviation": {"value": role["display_abbr"], "verification": role["display_abbr_verification"]},
        "analysis_token": analysis_token,
        "accepted_input_tokens": [analysis_token, *legacy_tokens],
        "ambiguity": copy.deepcopy(role.get("ambiguity", {"status": "none"})),
        "role_identity_status": identity_status,
        "behaviour_coverage": coverage_by_id.get(role["internal_id"], "identity_only"),
        "availability": availability,
    }


def roles_payload(phase: str | None = None, configured_position: str | None = None,
                  centre_back_line_count: int | None = None) -> Dict[str, Any]:
    if phase is not None and phase not in ("IP", "OOP"):
        raise ValueError("phase must be IP or OOP")
    catalog = role_constraints.load_role_catalog()
    knowledge = role_behaviours.load_knowledge_base()
    coverage_by_id = {row["internal_id"]: row["status"] for row in role_knowledge_coverage.build_coverage_report(catalog, knowledge)["roles"]}
    normalized_position = (positional_relationships.normalize_configured_position(configured_position)
                           if configured_position else None)
    context_key = normalized_position or configured_position
    contexts = POSITION_CONTEXTS.get(context_key, ((), ())) if context_key else None
    starting_positions, families = contexts if contexts is not None else ((), ())
    roles = []
    unavailable_roles = []
    unresolved_roles = []
    for role in catalog:
        if phase and role["phase"] != phase:
            continue
        if contexts is not None and not set(role["available_starting_positions"]) & set(starting_positions):
            continue
        if contexts is not None and families and not set(role["role_families"]) & set(families):
            continue
        public = _public_role(role, centre_back_line_count, coverage_by_id)
        if public["role_identity_status"] == "unresolved":
            unresolved_roles.append(public)
            continue
        if public["availability"]["status"] == "inactive":
            unavailable_roles.append(public)
            continue
        roles.append(public)
    return {"roles": roles, "phase": phase, "configured_position": context_key,
            "selector_context": {"available_starting_positions": list(starting_positions), "role_families": list(families)},
            "unavailable_roles": unavailable_roles, "unresolved_roles": unresolved_roles}


def analyze_payload(tactic: Any) -> Dict[str, Any]:
    if not isinstance(tactic, dict):
        raise ValueError("tactic must be a JSON object")
    validate_web_tactic_input(tactic)
    report = analyze_tactic_data(
        tactic, ROLE_DICTIONARY, ROLE_ALIASES,
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), source="web_api",
        team_instruction_catalog=validate_catalog(json.loads(TEAM_INSTRUCTION_CATALOG_PATH.read_text(encoding="utf-8-sig"))),
    )
    report["tactic_input"] = {
        "in_possession": {
            "formation": tactic.get("ip_formation"),
            "positions": list((tactic.get("ip_roles") or {}).keys()),
            "roles": copy.deepcopy(tactic.get("ip_roles") or {}),
            "team_instructions": copy.deepcopy(tactic.get("ip_team_instructions") or {}),
        },
        "out_of_possession": {
            "formation": tactic.get("oop_formation"),
            "positions": list((tactic.get("oop_roles") or {}).keys()),
            "roles": copy.deepcopy(tactic.get("oop_roles") or {}),
            "team_instructions": copy.deepcopy(tactic.get("oop_team_instructions") or {}),
            "editing_status": "limited",
        },
    }
    report["presentation"] = present_analysis(report)
    return report


def validate_web_tactic_input(tactic: Dict[str, Any]) -> None:
    """Validate only UI-supported IP role/position selections; OOP editing remains limited."""
    roles = tactic.get("ip_roles")
    if roles is None:
        return
    if not isinstance(roles, dict):
        raise ValueError("ip_roles must be an object")
    formation = tactic.get("ip_formation")
    positions = FORMATION_PRESETS.get(formation, list(roles))
    if formation in FORMATION_PRESETS and set(roles) != set(positions):
        raise ValueError("IP role positions must match the selected formation")
    count = centre_back_line_count(positions)
    for position, token in roles.items():
        if token is None:
            raise ValueError(f"Role selection is required for {position}")
        if not isinstance(token, str):
            raise ValueError(f"Invalid role selection for {position}")
        available = roles_payload("IP", position, count)["roles"]
        if not any(token in row["accepted_input_tokens"] for row in available):
            raise ValueError(f"Invalid role-position selection for {position}")


def evidence_sufficiency_payload(tactic: Any) -> Dict[str, Any]:
    """Read-only adapter for the existing core sufficiency report."""
    if not isinstance(tactic, dict):
        raise ValueError("tactic must be a JSON object")
    return build_current_tactic_evidence_sufficiency(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
