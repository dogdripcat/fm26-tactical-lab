# Progression Evaluator Phase 1

## Architecture and boundary

`progression_evaluator.py` and `web/static/js/progression_evaluator.js` consume the already-built Connectivity v2 node, structural-link, route, and qualitative route-family output. They never add a link, change a link, or replace `progression_routes`. The pipeline order is normalization → role resolution → Connectivity v2 → qualitative Connectivity → Progression. `progression_evaluation` is an additive JSON-compatible result.

The evaluator indexes existing directed structural links for reachability and removal simulation. That index is not a parallel tactical graph: no candidate relation is generated and no display/pitch coordinate is read.

## Occupied lines, advancement, gain, and skips

Occupied lines are the sorted configured `vertical_index` values present in the current IP formation. An existing `forward` structural link is an advancement event only if its target is on a later occupied line. Gain is the difference in occupied-line order, not the canonical numeric-band distance. A skip lists only occupied lines strictly between source and target. Therefore defensive line → midfield in a 4-4-2 has gain 1, while defensive line → forward skips the occupied midfield line.

`advancement_continuity` is `continuous` when every consecutive occupied-line transition has an existing reachable gain-1 event; `partial` when at least one but not all transitions are covered; otherwise `interrupted`. It is independent of the Connectivity qualitative line-continuity label.

## Profiles, regions, and highest reach

One profile is emitted for each existing qualitative Connectivity route family where available. A raw-route fallback is used only if no family is available. Profiles preserve family identity and report origin/destination bands and regions, events, gains, skips, regions used, and whether the existing route reaches attacking midfield or forward.

Global and left/centre/right highest reachable lines come only from frozen directed links. Regional status is descriptive: forward advancement, intermediate advancement, support/lateral-only access, or no structural advancement. No status ranks formations.

An explicit same-line, cross-region support link entering the source of a profile's first advancement is recorded as `lateral_transfers_before_advancement`. It is context only: the evaluator does not claim the support link is mandatory unless a future input contract provides such proof. `requires_transfer_from_another_region` stays `null` when current frozen structural data cannot prove necessity.

## Stall and dependency

An advance-then-stall requires a reachable advance into a non-forward structure and no later existing forward link from that receiver. The record includes stalled position/band, origin region, and support/recycle availability. It does not label a forward endpoint as a stall.

Progression dependency runs a separate node-removal simulation over existing links. It reports a node only when removal proves one of: all forward-line access removed, all central advancement removed, all multi-line progression removed, or the highest reachable line reduced. Shared route participation alone produces no dependency result.

## Role and ERS handling

The evaluator reports only existing verified semantic modifiers (`send_forward`, receiving, movement, half-space, and in-behind semantics). They explain possible use of an existing route; they cannot create topology, gains, skips, or occupied-line order. `move_into_halfspace` is exposed only as its explicit verified semantic. Expected Role Space remains separate and does not mutate the configured structural baseline.

## Synthetic coverage

`test_progression_evaluator.py` covers:

- A: connected support/recycle with no advancement
- B: staged occupied-line advancement
- C: true occupied-line skip
- D: canonical numeric gap without an occupied-line skip
- E/F: left-only and centre-only advancement
- G: explicit lateral support before advancement
- H: advance to midfield then stall
- I/J: same versus distinct route-family profiles
- K/L: shared connector without dependency versus proven progression dependency

## Seven preset snapshot

| Preset | Occupied lines | Highest | Profiles | Skips | Stalls | Dependencies |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 4-2-3-1 | GK, defensive, DM, AM, forward | forward | 12 | 0 | 0 | 0 |
| 4-3-3 | GK, defensive, DM, midfield, AM, forward | forward | 36 | 4 | 0 | 1 |
| 4-4-2 | GK, defensive, midfield, forward | forward | 12 | 0 | 0 | 0 |
| 4-2-4 | GK, defensive, midfield, AM, forward | forward | 12 | 4 | 0 | 0 |
| 3-4-2-1 | GK, defensive, wing-back, midfield, AM, forward | forward | 22 | 4 | 0 | 0 |
| 3-4-3 | GK, defensive, wing-back, midfield, AM, forward | forward | 16 | 4 | 0 | 0 |
| 3-5-2 | GK, defensive, wing-back, midfield, forward | forward | 18 | 2 | 0 | 0 |

These are structural descriptions, not formation ratings.

## Regression and parity

Connectivity v2 preset baselines remain 38/16, 40/48, 42/32, 38/32, 42/25, 38/20, and 48/40 links/routes respectively. Python/JavaScript parity is tested for Leicester, synthetic data, and all seven presets. No UI panel, CSS, HTML, score, team-instruction effect, player attribute, or match prediction was added.

## Files changed

- `progression_evaluator.py`
- `web/static/js/progression_evaluator.js`
- `web/static/js/progression_parity_runner.mjs`
- `core/pipeline.py`
- `web/static/js/tactic_analysis.js`
- `test_progression_evaluator.py`
- this report

## Limitations and repository state

Progression is configured structural reachability only. It cannot infer execution, pass selection, use frequency, player traits, team-instruction effects, actual positions, or whether a lateral transfer is required without stronger source data. No commit or push was performed.
