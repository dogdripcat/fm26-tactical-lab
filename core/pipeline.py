"""JSON-compatible pure analysis pipeline for future API adapters."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.tactic_normalization import normalize_tactic_data
import tactic_analysis
import connectivity_engine_v2
import connectivity_qualitative_evaluator
import progression_evaluator


def analyze_tactic_data(tactic: Dict[str, Any], role_dictionary: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str], catalog: List[Dict[str, Any]], behaviour_kb: List[Dict[str, Any]], observations: Any = None, source: str = "memory", team_instruction_catalog: Dict[str, Any] | None = None) -> Dict[str, Any]:
    normalized, changes = normalize_tactic_data(tactic, aliases, team_instruction_catalog)
    report = tactic_analysis.analyze_evidence(
        normalized, role_dictionary, aliases, observations, source, behaviour_kb, catalog,
    )
    report["normalization"] = {"changes": changes, "input_mutated": False}
    report["connectivity_v2"] = connectivity_engine_v2.build_connectivity_v2(normalized, catalog, behaviour_kb, aliases)
    report["connectivity_evaluation"] = connectivity_qualitative_evaluator.evaluate_connectivity_v2(report["connectivity_v2"])
    report["progression_evaluation"] = progression_evaluator.evaluate_progression(report["connectivity_v2"], report["connectivity_evaluation"])
    if team_instruction_catalog is not None:
        from core.team_instructions import input_status
        report["team_instruction_input_status"] = input_status(normalized, team_instruction_catalog)
    return report
