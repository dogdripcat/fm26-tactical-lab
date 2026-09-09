"""Pure tactic-data normalization. No filesystem, database, CLI, or print dependency."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple


def normalize_tactic_data(tactic: Dict[str, Any], aliases: Dict[Tuple[str, str], str]) -> tuple[Dict[str, Any], List[Dict[str, str]]]:
    if not isinstance(tactic, dict):
        raise ValueError("Tactic must be a JSON object")
    normalized = copy.deepcopy(tactic)
    changes = []
    for phase, key in (("IP", "ip_roles"), ("OOP", "oop_roles")):
        roles = normalized.get(key)
        if not isinstance(roles, dict):
            continue
        for position, value in roles.items():
            replacement = aliases.get((phase, value), value) if isinstance(value, str) else value
            if replacement != value:
                roles[position] = replacement
                changes.append({"phase": phase, "position": str(position), "before": value, "after": replacement})
    return normalized, changes
