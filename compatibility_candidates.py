"""Read-only compatibility candidate and rule-evidence readiness registry.

There is intentionally no compatibility evaluation or Connectivity integration
in this module. Candidate semantic evidence never becomes a production rule.
"""
from __future__ import annotations

import copy
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List


_ROOT = Path(__file__).resolve().parent
CANDIDATES_PATH = _ROOT / "compatibility_candidates.json"
RULE_EVIDENCE_PATH = _ROOT / "compatibility_rule_evidence.json"
SEMANTICS_PATH = _ROOT / "connectivity_semantic_vocabulary.json"
ERS_ONTOLOGY_PATH = _ROOT / "expected_role_space_ontology.json"
RULE_TYPES = frozenset(("distribution_reception", "space_creation_usage", "movement_space", "structural_support"))
PHASES = frozenset(("IP", "OOP"))
CANDIDATE_STATUSES = frozenset(("design_candidate", "evidence_present", "verified_rule", "unresolved"))
RELEVANCE = frozenset(("direct", "contextual", "none"))
RULE_EVIDENCE_VERIFICATIONS = frozenset(("evidence_present", "verified_rule", "unresolved"))
_CANDIDATE_KEYS = frozenset((
    "candidate_id", "rule_type", "phase", "source_selector", "target_selector",
    "required_context", "candidate_context_hypothesis", "connectivity_relevance",
    "partnership_relevance", "candidate_status", "production_eligible",
    "missing_evidence", "limitations",
))


def load_candidate_registry(path: str | Path = CANDIDATES_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_rule_evidence_registry(path: str | Path = RULE_EVIDENCE_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _vocabularies() -> tuple[set[str], Dict[str, set[str]]]:
    semantics = {item["semantic_id"] for item in json.loads(SEMANTICS_PATH.read_text(encoding="utf-8"))}
    ontology = json.loads(ERS_ONTOLOGY_PATH.read_text(encoding="utf-8"))
    return semantics, {field: set(values) for field, values in ontology["primitives"].items()}


def _validate_selector(selector: Dict[str, Any], semantics: set[str], ers: Dict[str, set[str]]) -> List[str]:
    if not isinstance(selector, dict):
        return ["selector_not_object"]
    selector_type = selector.get("selector_type")
    if selector_type == "semantic":
        if set(selector) != {"selector_type", "semantic_id"}:
            return ["semantic_selector_schema_invalid"]
        return [] if selector["semantic_id"] in semantics else ["unknown_semantic_selector"]
    if selector_type == "ers":
        if set(selector) != {"selector_type", "field", "concept_id"}:
            return ["ers_selector_schema_invalid"]
        return [] if selector.get("concept_id") in ers.get(selector.get("field"), set()) else ["unknown_ers_selector"]
    return ["role_name_or_unknown_selector_forbidden"]


def validate_candidate_registry(registry: Dict[str, Any], evidence_registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Validate candidates only; never turn them into executable rules."""
    errors: List[str] = []
    if not isinstance(registry, dict) or not isinstance(registry.get("candidates"), list):
        return {"valid": False, "errors": ["candidate_registry_schema_invalid"], "candidates": []}
    semantics, ers = _vocabularies()
    ids, definitions, reports = set(), set(), []
    for candidate in registry["candidates"]:
        item_errors = []
        if not isinstance(candidate, dict) or set(candidate) != _CANDIDATE_KEYS:
            item_errors.append("candidate_schema_invalid")
            candidate = candidate if isinstance(candidate, dict) else {}
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            item_errors.append("candidate_id_invalid")
        elif candidate_id in ids:
            item_errors.append("duplicate_candidate_id")
        ids.add(candidate_id)
        if candidate.get("rule_type") not in RULE_TYPES:
            item_errors.append("unknown_rule_type")
        if candidate.get("phase") not in PHASES:
            item_errors.append("phase_invalid")
        item_errors.extend("source_" + reason for reason in _validate_selector(candidate.get("source_selector"), semantics, ers))
        item_errors.extend("target_" + reason for reason in _validate_selector(candidate.get("target_selector"), semantics, ers))
        context = candidate.get("required_context")
        if not isinstance(context, dict) or set(context) != {"position_families", "configured_position_relations"} or not all(isinstance(context.get(key), list) and all(isinstance(v, str) for v in context[key]) for key in context):
            item_errors.append("required_context_invalid")
        if not isinstance(candidate.get("candidate_context_hypothesis"), dict):
            item_errors.append("candidate_context_hypothesis_invalid")
        if candidate.get("connectivity_relevance") not in RELEVANCE or candidate.get("partnership_relevance") not in RELEVANCE:
            item_errors.append("relevance_invalid")
        if candidate.get("candidate_status") not in CANDIDATE_STATUSES:
            item_errors.append("candidate_status_invalid")
        if not isinstance(candidate.get("production_eligible"), bool):
            item_errors.append("production_eligible_not_boolean")
        if not isinstance(candidate.get("missing_evidence"), list) or not all(isinstance(v, str) and v for v in candidate["missing_evidence"]):
            item_errors.append("missing_evidence_invalid")
        if not isinstance(candidate.get("limitations"), list) or not all(isinstance(v, str) and v for v in candidate["limitations"]):
            item_errors.append("limitations_invalid")
        definition = json.dumps({key: candidate.get(key) for key in ("rule_type", "phase", "source_selector", "target_selector")}, sort_keys=True)
        if definition in definitions:
            item_errors.append("duplicate_candidate_definition")
        definitions.add(definition)
        reports.append({"candidate_id": candidate_id, "schema_valid": not item_errors, "errors": item_errors})
        errors.extend(f"{candidate_id}:{reason}" for reason in item_errors)
    evidence_validation = validate_rule_evidence_registry(evidence_registry, ids) if evidence_registry is not None else {"valid": True, "errors": []}
    errors.extend(evidence_validation["errors"])
    return {"valid": not errors, "errors": errors, "candidates": reports}


def validate_rule_evidence_registry(registry: Dict[str, Any] | None, candidate_ids: set[str] | None = None) -> Dict[str, Any]:
    if registry is None:
        return {"valid": True, "errors": [], "evidence": []}
    if not isinstance(registry, dict) or not isinstance(registry.get("evidence"), list):
        return {"valid": False, "errors": ["rule_evidence_registry_schema_invalid"], "evidence": []}
    errors, ids, reports = [], set(), []
    required = {"rule_evidence_id", "source_kind", "verification", "title", "source", "accessed", "claim", "supports_candidate_ids", "limitations"}
    for evidence in registry["evidence"]:
        item_errors = []
        if not isinstance(evidence, dict) or set(evidence) != required:
            item_errors.append("rule_evidence_schema_invalid")
            evidence = evidence if isinstance(evidence, dict) else {}
        evidence_id = evidence.get("rule_evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.startswith("COMP_RULE_EVIDENCE_"):
            item_errors.append("rule_evidence_namespace_invalid")
        elif evidence_id in ids:
            item_errors.append("duplicate_rule_evidence_id")
        ids.add(evidence_id)
        if evidence.get("source_kind") not in {"user_ingame", "official", "experimental", "community"}:
            item_errors.append("rule_evidence_source_kind_invalid")
        if evidence.get("verification") not in RULE_EVIDENCE_VERIFICATIONS:
            item_errors.append("rule_evidence_verification_invalid")
        if not all(isinstance(evidence.get(key), str) and evidence[key] for key in ("title", "source", "claim")):
            item_errors.append("rule_evidence_text_invalid")
        try:
            datetime.date.fromisoformat(evidence.get("accessed"))
        except (TypeError, ValueError):
            item_errors.append("rule_evidence_accessed_invalid")
        supported = evidence.get("supports_candidate_ids")
        if not isinstance(supported, list) or not supported or not all(isinstance(item, str) and item for item in supported):
            item_errors.append("rule_evidence_supported_candidates_invalid")
        elif candidate_ids is not None and not set(supported) <= candidate_ids:
            item_errors.append("unknown_candidate_evidence_reference")
        if not isinstance(evidence.get("limitations"), list) or not all(isinstance(item, str) and item for item in evidence["limitations"]):
            item_errors.append("rule_evidence_limitations_invalid")
        reports.append({"rule_evidence_id": evidence_id, "valid": not item_errors, "errors": item_errors})
        errors.extend(f"{evidence_id}:{reason}" for reason in item_errors)
    return {"valid": not errors, "errors": errors, "evidence": reports}


def compatibility_candidate_readiness(candidate_registry: Dict[str, Any] | None = None,
                                      evidence_registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Calculate registry readiness without applying a candidate to any role pair."""
    candidates = load_candidate_registry() if candidate_registry is None else copy.deepcopy(candidate_registry)
    evidence = load_rule_evidence_registry() if evidence_registry is None else copy.deepcopy(evidence_registry)
    validation = validate_candidate_registry(candidates, evidence)
    evidence_by_candidate: Dict[str, List[Dict[str, Any]]] = {}
    for item in evidence.get("evidence", []) if isinstance(evidence, dict) else []:
        for candidate_id in item.get("supports_candidate_ids", []) if isinstance(item, dict) else []:
            evidence_by_candidate.setdefault(candidate_id, []).append(item)
    by_rule_type, by_status, missing, details = {}, {}, {}, []
    candidate_validity = {item["candidate_id"]: item for item in validation["candidates"]}
    for candidate in candidates.get("candidates", []) if isinstance(candidates, dict) else []:
        candidate_id = candidate.get("candidate_id")
        schema = candidate_validity.get(candidate_id, {"schema_valid": False})
        linked = evidence_by_candidate.get(candidate_id, [])
        verified_count = sum(item.get("verification") == "verified_rule" for item in linked)
        reasons = []
        if not schema["schema_valid"]:
            reasons.append("candidate_schema_or_selector_invalid")
        if not linked:
            reasons.append("missing_compatibility_rule_evidence")
        if not verified_count:
            reasons.append("missing_verified_rule_evidence")
        if candidate.get("candidate_status") != "verified_rule":
            reasons.append("candidate_not_verified_rule")
        if candidate.get("missing_evidence"):
            reasons.append("declared_missing_evidence")
        if any(item.get("verification") == "unresolved" for item in linked):
            reasons.append("unresolved_rule_evidence")
        eligible = not reasons
        by_rule_type[candidate.get("rule_type", "invalid")] = by_rule_type.get(candidate.get("rule_type", "invalid"), 0) + 1
        by_status[candidate.get("candidate_status", "invalid")] = by_status.get(candidate.get("candidate_status", "invalid"), 0) + 1
        for reason in reasons:
            missing[reason] = missing.get(reason, 0) + 1
        details.append({
            "candidate_id": candidate_id, "schema_valid": schema["schema_valid"],
            "selectors_valid": schema["schema_valid"] and not any("selector" in reason for reason in schema.get("errors", [])),
            "rule_evidence_count": len(linked), "verified_rule_evidence_count": verified_count,
            "production_eligible": eligible, "blocking_reasons": reasons,
        })
    total = len(details)
    eligible = sum(item["production_eligible"] for item in details)
    return {
        "candidates_total": total, "rule_evidence_total": len(evidence.get("evidence", [])) if isinstance(evidence, dict) else 0,
        "production_eligible": eligible, "not_production_eligible": total - eligible,
        "by_rule_type": by_rule_type, "by_status": by_status, "missing_evidence": missing,
        "registry_valid": validation["valid"], "registry_errors": validation["errors"], "candidates": details,
    }
