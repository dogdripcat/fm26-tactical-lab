"""Pure, evidence-only Expected Role Space (ERS) projection.

ERS is supplementary metadata.  It does not infer configured positions,
movement coordinates, compatibility, connectivity, or tactical scores.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List

import positional_relationships
import role_behaviours
import role_constraints


_ROOT = Path(__file__).resolve().parent
_ONTOLOGY_PATH = _ROOT / "expected_role_space_ontology.json"
_VOCABULARY_PATH = _ROOT / "connectivity_semantic_vocabulary.json"
_FIELDS = ("occupancy", "reception_spaces", "movement_targets", "movement_directions", "structural_effects", "exclusions")
_VERIFIED = frozenset(("verified", "official", "user_ingame_verified"))
_SUPPORTED_LIMITATION = "등록된 항목은 검증된 역할 설명의 일부이며 전체 역할 움직임을 뜻하지 않는다."


def load_expected_role_space_ontology(path: str | Path | None = None,
                                      vocabulary_path: str | Path | None = None) -> Dict[str, Any]:
    source = _ONTOLOGY_PATH if path is None else Path(path)
    vocabulary_source = _VOCABULARY_PATH if vocabulary_path is None else Path(vocabulary_path)
    return validate_expected_role_space_ontology(
        json.loads(source.read_text(encoding="utf-8")),
        json.loads(vocabulary_source.read_text(encoding="utf-8")),
    )


def validate_expected_role_space_ontology(ontology: Dict[str, Any], vocabulary: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(ontology, dict) or not isinstance(ontology.get("primitives"), dict) or not isinstance(ontology.get("mappings"), list):
        raise ValueError("ERS ontology requires primitives and mappings")
    if set(ontology["primitives"]) != set(_FIELDS):
        raise ValueError("ERS primitive fields must match the supported output fields")
    for field, concepts in ontology["primitives"].items():
        if not isinstance(concepts, list) or not concepts or not all(isinstance(item, str) and item for item in concepts):
            raise ValueError("ERS primitive concepts must be non-empty strings")
        if len(concepts) != len(set(concepts)):
            raise ValueError("ERS primitive concepts must be unique within their field")
    semantic_ids = {item.get("semantic_id") for item in vocabulary if isinstance(item, dict)}
    mapping_ids, mapping_semantics = set(), set()
    for mapping in ontology["mappings"]:
        if not isinstance(mapping, dict) or set(mapping) != {"mapping_id", "semantic_id", "field", "concept_id"}:
            raise ValueError("ERS mapping schema is invalid")
        if not all(isinstance(mapping[key], str) and mapping[key] for key in mapping):
            raise ValueError("ERS mapping values must be non-empty strings")
        if mapping["mapping_id"] in mapping_ids or mapping["semantic_id"] in mapping_semantics:
            raise ValueError("ERS mappings must not duplicate mapping or semantic IDs")
        mapping_ids.add(mapping["mapping_id"])
        mapping_semantics.add(mapping["semantic_id"])
        if mapping["semantic_id"] not in semantic_ids:
            raise ValueError("ERS mapping references an unknown semantic ID")
        if mapping["field"] not in _FIELDS or mapping["concept_id"] not in ontology["primitives"][mapping["field"]]:
            raise ValueError("ERS mapping concept does not belong to its output field")
    return copy.deepcopy(ontology)


def _empty_space(status: str = "unknown", limitations: List[str] | None = None) -> Dict[str, Any]:
    return {
        "status": status,
        **{field: [] for field in _FIELDS},
        "limitations": list(limitations or []),
    }


def _catalog_index(catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {role["internal_id"]: role for role in role_constraints.validate_role_catalog(catalog)}


def _verified_behaviour_records(knowledge_base: List[Dict[str, Any]], catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only role-gated, individually verified records with provenance."""
    kb = role_behaviours.validate_knowledge_base(knowledge_base)
    allowed_ids = {
        behaviour["behaviour_id"]
        for entry in kb if entry["behaviour_verified"]
        for behaviour in entry["behaviours"] if behaviour["verification"] in _VERIFIED
    }
    return [record for record in role_behaviours.behaviour_records(kb, catalog)
            if record["behaviour_id"] in allowed_ids and record["verification"] in _VERIFIED
            and record["role_internal_id"] and record["evidence_ids"]]


def build_expected_role_space(role_internal_id: str | None, phase: str,
                              catalog: List[Dict[str, Any]] | None = None,
                              knowledge_base: List[Dict[str, Any]] | None = None,
                              ontology: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Project explicit verified semantic mappings for one resolved role only."""
    if phase not in ("IP", "OOP"):
        raise ValueError("phase must be IP or OOP")
    catalog = role_constraints.load_role_catalog() if catalog is None else role_constraints.validate_role_catalog(catalog)
    knowledge_base = role_behaviours.load_knowledge_base() if knowledge_base is None else role_behaviours.validate_knowledge_base(knowledge_base)
    ontology = load_expected_role_space_ontology() if ontology is None else ontology
    vocabulary = json.loads(_VOCABULARY_PATH.read_text(encoding="utf-8"))
    ontology = validate_expected_role_space_ontology(ontology, vocabulary)
    role = _catalog_index(catalog).get(role_internal_id) if role_internal_id else None
    if role is None:
        return {"role_internal_id": role_internal_id, "phase": phase, "expected_role_space": _empty_space(
            limitations=["역할이 해결되지 않아 expected role space를 생성하지 않았다."])}
    if role["phase"] != phase:
        raise ValueError("role_internal_id phase does not match requested phase")
    mappings = {item["semantic_id"]: item for item in ontology["mappings"]}
    output = _empty_space()
    for record in _verified_behaviour_records(knowledge_base, catalog):
        if record["role_internal_id"] != role_internal_id or record["phase"] != phase:
            continue
        for semantics in record["connectivity_semantics"].values():
            for semantic in semantics:
                mapping = mappings.get(semantic["semantic_id"])
                if mapping is None or semantic.get("verification") not in _VERIFIED or not semantic.get("evidence_ids"):
                    continue
                output[mapping["field"]].append({
                    "concept_id": mapping["concept_id"],
                    "semantic_id": semantic["semantic_id"],
                    "behaviour_ids": [record["behaviour_id"]],
                    "evidence_ids": copy.deepcopy(semantic["evidence_ids"]),
                    "verification": semantic["verification"],
                })
    if any(output[field] for field in _FIELDS):
        output["status"] = "supported"
        output["limitations"] = [_SUPPORTED_LIMITATION]
    else:
        output["limitations"] = ["검증된 semantic 중 Expected Role Space ontology mapping이 적용되는 항목이 없다."]
    return {"role_internal_id": role_internal_id, "phase": phase, "expected_role_space": output}


def build_position_context_with_expected_role_space(phase: str, configured_position: str,
                                                    role_internal_id: str | None,
                                                    catalog: List[Dict[str, Any]] | None = None,
                                                    knowledge_base: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Present immutable configured-position context beside, never inside, ERS."""
    node = positional_relationships.build_position_node(phase, configured_position, role_internal_id)
    context = {key: node[key] for key in (
        "configured_position", "position_family", "vertical_band", "vertical_index", "lateral_slot",
    )}
    return {
        "configured_position_context": context,
        **build_expected_role_space(role_internal_id, phase, catalog, knowledge_base),
    }


def expected_role_space_coverage(catalog: List[Dict[str, Any]] | None = None,
                                 knowledge_base: List[Dict[str, Any]] | None = None,
                                 ontology: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Report actual ERS mapping coverage. by_field counts generated provenance items."""
    catalog = role_constraints.load_role_catalog() if catalog is None else role_constraints.validate_role_catalog(catalog)
    knowledge_base = role_behaviours.load_knowledge_base() if knowledge_base is None else role_behaviours.validate_knowledge_base(knowledge_base)
    ontology = load_expected_role_space_ontology() if ontology is None else ontology
    vocabulary = json.loads(_VOCABULARY_PATH.read_text(encoding="utf-8"))
    ontology = validate_expected_role_space_ontology(ontology, vocabulary)
    report = {
        "roles_total": len(catalog), "supported": 0, "unknown": 0,
        "by_phase": {"IP": {"supported": 0, "unknown": 0}, "OOP": {"supported": 0, "unknown": 0}},
        "by_field": {field: 0 for field in _FIELDS},
        "unmapped_semantics": [copy.deepcopy(item) for item in vocabulary
                                if item["semantic_id"] not in {mapping["semantic_id"] for mapping in ontology["mappings"]}],
    }
    for role in catalog:
        result = build_expected_role_space(role["internal_id"], role["phase"], catalog, knowledge_base, ontology)["expected_role_space"]
        status = result["status"]
        report[status] += 1
        report["by_phase"][role["phase"]][status] += 1
        for field in _FIELDS:
            report["by_field"][field] += len(result[field])
    return report
