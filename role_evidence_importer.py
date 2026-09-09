"""Fail-closed import preparation for manually reviewed FM26 role evidence packages."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import role_behaviours
import role_constraints
import role_knowledge_coverage


VOCABULARY_PATH = Path(__file__).resolve().with_name("connectivity_semantic_vocabulary.json")


def load_vocabulary(path: Path = VOCABULARY_PATH) -> Dict[str, str]:
    rows = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return {row["semantic_id"]: row["group"] for row in rows}


def validate_role_evidence(package: Any, catalog: List[Dict[str, Any]], behaviour_kb: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate and stage a merge without modifying caller objects or files."""
    errors: List[str] = []
    warnings: List[str] = []
    changes = {"roles_changed": [], "behaviours_added": 0, "semantic_mappings_added": 0, "evidence_added": 0}
    try:
        catalog = role_constraints.validate_role_catalog(catalog)
        behaviour_kb = role_behaviours.validate_knowledge_base(behaviour_kb)
        _validate_package_shape(package)
        role = next((row for row in catalog if row["internal_id"] == package["role_internal_id"]), None)
        if role is None:
            raise ValueError("unknown role_internal_id")
        if package["phase"] != role["phase"]:
            raise ValueError("package phase does not match catalog role")
        if package["role_name_ko"] != role["role_name_ko"]:
            raise ValueError("package role_name_ko does not match catalog role")
        if package["source_kind"] not in ("user_ingame", "official"):
            raise ValueError("source_kind must be user_ingame or official")
        if any(key in package for key in ("display_abbr", "abbr", "ingame_abbr")):
            raise ValueError("packages may not add or alter abbreviations")
        evidence = _validate_evidence(package)
        existing_evidence = {item["evidence_id"] for row in behaviour_kb for item in row["evidence"]}
        existing_evidence |= {item["evidence_id"] for row in catalog for item in row["evidence"]}
        if evidence["evidence_id"] in existing_evidence:
            raise ValueError("duplicate evidence_id")
        vocabulary = load_vocabulary()
        staged_catalog = copy.deepcopy(catalog)
        staged_kb = copy.deepcopy(behaviour_kb)
        staged_role = next(row for row in staged_catalog if row["internal_id"] == role["internal_id"])
        staged_role["evidence"].append(copy.deepcopy(evidence))
        changes["evidence_added"] = 1
        changes["roles_changed"].append(role["internal_id"])
        _merge_constraints(package["formation_constraints"], staged_role, evidence["evidence_id"])
        entry = _entry_for_role(staged_kb, staged_role)
        _merge_metadata(package, entry, evidence["evidence_id"])
        for raw in package["behaviours"]:
            behaviour = _normalise_behaviour(raw, package["phase"], evidence["evidence_id"], vocabulary, package["source_kind"])
            existing = next((item for item in entry["behaviours"] if item["behaviour_id"] == behaviour["behaviour_id"]), None)
            if existing is not None:
                if _behaviour_signature(existing) != _behaviour_signature(behaviour):
                    raise ValueError("behaviour_id conflict")
                if evidence["evidence_id"] not in existing["evidence_ids"]:
                    existing["evidence_ids"].append(evidence["evidence_id"])
                _merge_semantic_provenance(existing, behaviour, evidence["evidence_id"])
                continue
            entry["behaviours"].append(behaviour)
            changes["behaviours_added"] += 1
            changes["semantic_mappings_added"] += sum(len(items) for items in behaviour.get("connectivity_semantics", {}).values())
        entry["evidence"].append(copy.deepcopy(evidence))
        entry["behaviour_verified"] = bool(entry["behaviours"])
        if entry["behaviours"]:
            entry["coverage_status"] = "partial"
        role_constraints.validate_role_catalog(staged_catalog)
        role_behaviours.validate_knowledge_base(staged_kb)
        before = _coverage_counts(catalog, behaviour_kb)
        after = _coverage_counts(staged_catalog, staged_kb)
        return {"valid": True, "warnings": warnings, "errors": errors, "proposed_changes": {**changes, "coverage_before": before, "coverage_after": after}, "_catalog": staged_catalog, "_behaviour_kb": staged_kb}
    except (TypeError, ValueError, KeyError) as exc:
        errors.append(str(exc))
        return {"valid": False, "warnings": warnings, "errors": errors, "proposed_changes": {**changes, "coverage_before": _coverage_counts_safe(catalog, behaviour_kb), "coverage_after": {}}}


def public_report(result: Dict[str, Any]) -> Dict[str, Any]:
    """Remove staged private data before console or web presentation."""
    return {key: copy.deepcopy(value) for key, value in result.items() if not key.startswith("_")}


def apply_role_evidence(package: Any, catalog_path: Path, behaviour_path: Path) -> Dict[str, Any]:
    """Validate fully, then replace both JSON files. No write occurs on validation failure."""
    catalog = role_constraints.load_role_catalog(catalog_path)
    behaviour_kb = role_behaviours.load_knowledge_base(behaviour_path)
    result = validate_role_evidence(package, catalog, behaviour_kb)
    if not result["valid"]:
        return public_report(result)
    _write_json_new(result["_catalog"], Path(catalog_path))
    _write_json_new(result["_behaviour_kb"], Path(behaviour_path))
    return public_report(result)


def apply_role_evidence_packages(packages: List[Any], catalog_path: Path, behaviour_path: Path) -> Dict[str, Any]:
    """Stage every package first, then write both stores once; package batch is atomic."""
    catalog = role_constraints.load_role_catalog(catalog_path)
    kb = role_behaviours.load_knowledge_base(behaviour_path)
    before = _coverage_counts(catalog, kb)
    staged_catalog, staged_kb = catalog, kb
    reports = []
    totals = {"roles_changed": [], "behaviours_added": 0, "semantic_mappings_added": 0, "evidence_added": 0}
    for package in packages:
        result = validate_role_evidence(package, staged_catalog, staged_kb)
        reports.append(public_report(result))
        if not result["valid"]:
            return {"valid": False, "packages": reports, "errors": result["errors"], "proposed_changes": {**totals, "coverage_before": before, "coverage_after": {}}}
        staged_catalog, staged_kb = result["_catalog"], result["_behaviour_kb"]
        change = result["proposed_changes"]
        totals["roles_changed"].extend(change["roles_changed"])
        for key in ("behaviours_added", "semantic_mappings_added", "evidence_added"):
            totals[key] += change[key]
    _write_json_new(staged_catalog, Path(catalog_path))
    _write_json_new(staged_kb, Path(behaviour_path))
    return {"valid": True, "packages": reports, "errors": [], "proposed_changes": {**totals, "coverage_before": before, "coverage_after": _coverage_counts(staged_catalog, staged_kb)}}


def _validate_package_shape(package: Any) -> None:
    required = {"role_internal_id", "phase", "role_name_ko", "source_kind", "evidence_id", "evidence", "role_description", "role_tags", "player_instructions", "key_attributes", "formation_constraints", "behaviours"}
    if not isinstance(package, dict) or not required <= package.keys():
        raise ValueError("invalid role evidence package shape")
    if package["phase"] not in ("IP", "OOP") or not all(isinstance(package[key], str) and package[key].strip() for key in ("role_internal_id", "role_name_ko", "source_kind", "evidence_id", "role_description")):
        raise ValueError("invalid package identity")
    for field in ("role_tags", "player_instructions", "key_attributes", "formation_constraints", "behaviours"):
        if not isinstance(package[field], list):
            raise ValueError(field + " must be an array")
    if not all(isinstance(item, str) and item.strip() for item in package["role_tags"] + package["key_attributes"]):
        raise ValueError("role tags and key attributes must be names only")


def _validate_evidence(package: Dict[str, Any]) -> Dict[str, Any]:
    evidence = package["evidence"]
    required = {"evidence_id", "source_type", "title", "source", "accessed", "notes"}
    if not isinstance(evidence, dict) or not required <= evidence.keys() or evidence["evidence_id"] != package["evidence_id"]:
        raise ValueError("invalid package evidence")
    if package["source_kind"] == "user_ingame" and evidence["source_type"] != "user_ingame_capture":
        raise ValueError("user_ingame package requires user_ingame_capture evidence")
    if package["source_kind"] == "official":
        if evidence["source_type"] != "official":
            raise ValueError("official package requires official evidence")
        if not evidence.get("source", "").startswith("https://www.footballmanager.com/"):
            raise ValueError("official package requires a Football Manager official URL")
    try:
        date.fromisoformat(evidence["accessed"])
    except (TypeError, ValueError) as exc:
        raise ValueError("evidence accessed must be YYYY-MM-DD") from exc
    return copy.deepcopy(evidence)


def _merge_constraints(constraints: List[Any], role: Dict[str, Any], evidence_id: str) -> None:
    for constraint in constraints:
        if not isinstance(constraint, dict):
            raise ValueError("invalid formation constraint")
        item = copy.deepcopy(constraint)
        item.setdefault("phase", role["phase"])
        item.setdefault("verification", "user_ingame_verified")
        item.setdefault("evidence_ids", [evidence_id])
        if item["phase"] != role["phase"]:
            raise ValueError("formation constraint phase mismatch")
        if item not in role["formation_constraints"]:
            role["formation_constraints"].append(item)


def _entry_for_role(kb: List[Dict[str, Any]], role: Dict[str, Any]) -> Dict[str, Any]:
    reference = role["role_behaviour_ref"]
    if reference:
        entry = next((item for item in kb if item["phase"] == reference["phase"] and item["role"] == reference["role"]), None)
        if entry:
            return entry
    token = role["display_abbr"] or role["internal_id"]
    entry = {"role": token, "role_internal_id": role["internal_id"], "phase": role["phase"], "behaviours": [], "relationships": [], "evidence": [], "behaviour_verified": False, "coverage_status": "partial"}
    kb.append(entry)
    role["role_behaviour_ref"] = {"phase": role["phase"], "role": token}
    return entry


def _merge_metadata(package: Dict[str, Any], entry: Dict[str, Any], evidence_id: str) -> None:
    verification = _verification_for_source_kind(package["source_kind"])
    entry.setdefault("imported_role_description", []).append({"description_ko": package["role_description"], "evidence_ids": [evidence_id], "verification": verification})
    entry.setdefault("imported_role_tags", []).extend({"name_ko": tag, "evidence_ids": [evidence_id]} for tag in package["role_tags"])
    entry.setdefault("key_attributes", []).extend({"name": name, "evidence_ids": [evidence_id]} for name in package["key_attributes"])
    for instruction in package["player_instructions"]:
        if not isinstance(instruction, dict):
            raise ValueError("invalid player instruction")
        item = copy.deepcopy(instruction)
        item.setdefault("phase", entry["phase"]); item.setdefault("evidence_ids", [evidence_id]); item.setdefault("verification", verification)
        if item not in entry.setdefault("player_instructions", []): entry["player_instructions"].append(item)


def _normalise_behaviour(raw: Any, phase: str, evidence_id: str, vocabulary: Dict[str, str], source_kind: str = "user_ingame") -> Dict[str, Any]:
    if not isinstance(raw, dict) or not isinstance(raw.get("behaviour_id"), str) or not isinstance(raw.get("claim"), str):
        raise ValueError("invalid behaviour package entry")
    semantics: Dict[str, List[Dict[str, Any]]] = {}
    for mapping in raw.get("semantic_mappings", []):
        if not isinstance(mapping, dict) or mapping.get("semantic_id") not in vocabulary:
            raise ValueError("unknown semantic_id")
        group = mapping.get("group", vocabulary[mapping["semantic_id"]])
        if group != vocabulary[mapping["semantic_id"]]:
            raise ValueError("semantic group does not match vocabulary")
        semantics.setdefault(group, []).append({"semantic_id": mapping["semantic_id"], "evidence_ids": [evidence_id], "verification": _verification_for_source_kind(source_kind)})
    item = {"behaviour_id": raw["behaviour_id"], "category": raw.get("category", "role_description"), "claim": raw["claim"], "conditions": raw.get("conditions", ["in_possession" if phase == "IP" else "out_of_possession"]), "evidence_ids": [evidence_id], "verification": _verification_for_source_kind(source_kind)}
    if semantics: item["connectivity_semantics"] = semantics
    return item


def _behaviour_signature(item: Dict[str, Any]) -> Dict[str, Any]:
    semantics = {group: sorted(semantic["semantic_id"] for semantic in items)
                 for group, items in item.get("connectivity_semantics", {}).items()}
    return {"category": item.get("category"), "claim": item.get("claim"),
            "conditions": copy.deepcopy(item.get("conditions", [])), "connectivity_semantics": semantics}


def _merge_semantic_provenance(existing: Dict[str, Any], incoming: Dict[str, Any], evidence_id: str) -> None:
    """Add corroborating evidence to an existing identical semantic, never a new semantic ID."""
    for group, incoming_items in incoming.get("connectivity_semantics", {}).items():
        existing_items = existing.setdefault("connectivity_semantics", {}).setdefault(group, [])
        for incoming_item in incoming_items:
            current = next((item for item in existing_items if item["semantic_id"] == incoming_item["semantic_id"]), None)
            if current is None:
                existing_items.append(copy.deepcopy(incoming_item))
            elif evidence_id not in current["evidence_ids"]:
                current["evidence_ids"].append(evidence_id)


def _verification_for_source_kind(source_kind: str) -> str:
    return "official" if source_kind == "official" else "user_ingame_verified"


def _coverage_counts(catalog: List[Dict[str, Any]], kb: List[Dict[str, Any]]) -> Dict[str, int]:
    report = role_knowledge_coverage.build_coverage_report(catalog, kb)
    return {key: report[key] for key in ("total_roles", "verified", "partial", "identity_only", "unresolved")}


def _coverage_counts_safe(catalog: Any, kb: Any) -> Dict[str, int]:
    try: return _coverage_counts(catalog, kb)
    except (TypeError, ValueError, KeyError): return {}


def _write_json_new(data: Any, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".importing")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
