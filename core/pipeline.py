"""JSON-compatible pure analysis pipeline for future API adapters."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.tactic_normalization import normalize_tactic_data
import tactic_analysis


def analyze_tactic_data(tactic: Dict[str, Any], role_dictionary: List[Dict[str, Any]], aliases: Dict[Tuple[str, str], str], catalog: List[Dict[str, Any]], behaviour_kb: List[Dict[str, Any]], observations: Any = None, source: str = "memory") -> Dict[str, Any]:
    normalized, changes = normalize_tactic_data(tactic, aliases)
    report = tactic_analysis.analyze_evidence(
        normalized, role_dictionary, aliases, observations, source, behaviour_kb, catalog,
    )
    report["normalization"] = {"changes": changes, "input_mutated": False}
    return report
