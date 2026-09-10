"""Display-only football-pitch coordinates for the web UI.

This module does not participate in configured-position or Connectivity logic.
"""
from __future__ import annotations

import copy
from typing import Dict, Iterable

CENTER_X = 50.0
_BASE = {
    "GK": (50, 91), "LB": (16, 74), "LCB": (38, 77), "CB": (50, 77), "DC": (50, 77), "RCB": (62, 77), "RB": (84, 74),
    "wing_back_left": (13, 62), "wing_back_right": (87, 62),
    "DML": (37, 61), "DM": (50, 61), "DMR": (63, 61),
    "MCL": (38, 49), "MC": (50, 49), "MCR": (62, 49), "ML": (17, 48), "MR": (83, 48),
    "AML": (20, 30), "AMC": (50, 30), "AMR": (80, 30), "ST": (50, 12), "CF": (50, 12),
}


def formation_coordinates(positions: Iterable[str]) -> Dict[str, list[float]]:
    """Create bounded, symmetric display coordinates for one configured formation."""
    positions = list(positions)
    result = {position: list(_BASE[position]) for position in positions if position in _BASE}
    forwards = [position for position in ("ST", "CF") if position in result]
    if len(forwards) == 2:
        result["ST"][0], result["CF"][0] = 42, 58
    elif len(forwards) == 1:
        result[forwards[0]][0] = CENTER_X
    return result


def validate_layout(layout: Dict[str, Dict[str, list[float]]]) -> None:
    for positions in layout.values():
        for x, y in positions.values():
            if not 0 <= x <= 100 or not 0 <= y <= 100:
                raise ValueError("Pitch coordinate must be inside the display bounds")


def payload(presets: Dict[str, list[str]]) -> Dict[str, object]:
    layout = {name: formation_coordinates(positions) for name, positions in presets.items()}
    validate_layout(layout)
    return {"center_x": CENTER_X, "coordinates": copy.deepcopy(layout), "display_only": True}
