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


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "sample_leicester_4231.json"
POSITION_REGISTRY_PATH = ROOT / "configured_position_registry.json"
# UI position contexts are broad catalog starting-position labels, not role rules.
# These contexts adapt existing registry position IDs to existing catalog fields.
# They do not define role behaviour, expected movement, or Connectivity.
POSITION_CONTEXTS = {
    "GK": (("Goalkeeper",), ("Goalkeeper",)),
    "LB": (("Full-Back", "Wing-Back"), ("Full-Back", "Wing-Back")),
    "RB": (("Full-Back", "Wing-Back"), ("Full-Back", "Wing-Back")),
    "LCB": (("D(C)",), ("Centre-Back",)), "CB": (("D(C)",), ("Centre-Back",)),
    "RCB": (("D(C)",), ("Centre-Back",)),
    "DML": (("DM",), ("DM",)), "DM": (("DM",), ("DM",)), "DMR": (("DM",), ("DM",)),
    "MCL": (("CM",), ("CM",)), "MC": (("CM",), ("CM",)), "MCR": (("CM",), ("CM",)),
    "ML": (("Wide Midfield",), ("Wide Midfield",)), "MR": (("Wide Midfield",), ("Wide Midfield",)),
    "AML": (("Winger",), ("Winger",)), "AMC": (("AM",), ("AM",)), "AMR": (("Winger",), ("Winger",)),
    "ST": (("FW",), ("FW",)), "CF": (("FW",), ("FW",)),
}

# Presets are configured-position arrays only. They carry no role selection or analysis rule.
FORMATION_PRESETS = {
    "4-2-3-1": ["GK", "LB", "LCB", "RCB", "RB", "DML", "DMR", "AML", "AMC", "AMR", "ST"],
    "4-3-3": ["GK", "LB", "LCB", "RCB", "RB", "DM", "MCL", "MCR", "AML", "AMR", "ST"],
    "4-4-2": ["GK", "LB", "LCB", "RCB", "RB", "ML", "MCL", "MCR", "MR", "ST", "CF"],
    "4-2-4": ["GK", "LB", "LCB", "RCB", "RB", "MCL", "MCR", "AML", "AMR", "ST", "CF"],
    "3-4-2-1": ["GK", "LCB", "CB", "RCB", "ML", "MR", "DML", "DMR", "AML", "AMC", "ST"],
    "3-4-3": ["GK", "LCB", "CB", "RCB", "ML", "MR", "DML", "DMR", "AML", "AMR", "ST"],
    "3-5-2": ["GK", "LCB", "CB", "RCB", "ML", "MR", "DML", "DMR", "AMC", "ST", "CF"],
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


def sample_tactic() -> Dict[str, Any]:
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8-sig"))


def _public_role(role: Dict[str, Any], centre_back_line_count: int | None, coverage_by_id: Dict[str, str]) -> Dict[str, Any]:
    availability = role_constraints.role_availability(role, centre_back_line_count)
    verified_abbr = role["display_abbr"] if role["display_abbr_verification"] == "user_ingame_verified" else None
    analysis_token = verified_abbr or role["internal_id"]
    legacy_tokens = [token for (phase, token), canonical in ROLE_ALIASES.items()
                     if phase == role["phase"] and canonical == verified_abbr]
    return {
        "role_internal_id": role["internal_id"], "phase": role["phase"],
        "role_name_ko": role["role_name_ko"], "role_families": copy.deepcopy(role["role_families"]),
        "available_starting_positions": copy.deepcopy(role["available_starting_positions"]),
        "abbreviation": {"value": role["display_abbr"], "verification": role["display_abbr_verification"]},
        "analysis_token": analysis_token,
        "accepted_input_tokens": [analysis_token, *legacy_tokens],
        "ambiguity": copy.deepcopy(role.get("ambiguity", {"status": "none"})),
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
    contexts = POSITION_CONTEXTS.get(configured_position.upper(), ((), ())) if configured_position else None
    starting_positions, families = contexts if contexts is not None else ((), ())
    roles = []
    unavailable_roles = []
    for role in catalog:
        if phase and role["phase"] != phase:
            continue
        if contexts is not None and (not set(role["available_starting_positions"]) & set(starting_positions)
                                 or not set(role["role_families"]) & set(families)):
            continue
        public = _public_role(role, centre_back_line_count, coverage_by_id)
        if public["availability"]["status"] == "inactive":
            unavailable_roles.append(public)
            continue
        roles.append(public)
    return {"roles": roles, "phase": phase, "configured_position": configured_position,
            "selector_context": {"available_starting_positions": list(starting_positions), "role_families": list(families)},
            "unavailable_roles": unavailable_roles}


def analyze_payload(tactic: Any) -> Dict[str, Any]:
    if not isinstance(tactic, dict):
        raise ValueError("tactic must be a JSON object")
    return analyze_tactic_data(
        tactic, ROLE_DICTIONARY, ROLE_ALIASES,
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), source="web_api",
    )


def evidence_sufficiency_payload(tactic: Any) -> Dict[str, Any]:
    """Read-only adapter for the existing core sufficiency report."""
    if not isinstance(tactic, dict):
        raise ValueError("tactic must be a JSON object")
    return build_current_tactic_evidence_sufficiency(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
