# Connectivity v2 Baseline

- Freeze date: 2026-09-12
- Purpose: Freeze the completed Connectivity v2 qualitative-analysis baseline before later tactical dimensions are considered.

## Architecture

Connectivity v2 is a position-first, score-free pipeline:

1. Positional structural topology builds directed candidate links from configured IP positions.
2. Occupied-line adjacency admits verified line-adjacent structural links without role-name inference.
3. Progression routes are derived from that structural topology.
4. The display-priority layer exposes a readable default subset and preserves the complete structural graph in full mode.
5. The qualitative evaluator reports continuity, regional routes, support/recycle, dependencies, bottlenecks, dead ends, and isolated positions without changing topology.
6. The static UI presents only evaluator output and retained structural-link provenance.

## Freeze status

- Occupied-line adjacency repair: frozen and regression-tested.
- Display-priority layer: frozen; primary/full rendering does not alter analysis truth.
- Qualitative evaluator: frozen; no numerical Connectivity score exists.
- User-facing UI: frozen following the visual acceptance audit.
- Visual Acceptance result: `READY_TO_FREEZE`.
- Unittest baseline: 216 passed.

## Known limitations

Connectivity v2 describes structural connection possibilities. It does not predict actual pass success, player execution, attributes, opponent pressure, match context, possession, chance volume, or performance.

The Forward-role catalogue blocker remains unresolved: unverified forward roles are not guessed merely for selector completeness. Team Instruction tactical effects remain unmodelled. No numerical Connectivity score is calculated.

## Change-control rule

Future tactical dimensions must not silently redefine Connectivity v2 semantics. Any future behavioural change to Connectivity must be separately documented and regression-tested against this baseline.