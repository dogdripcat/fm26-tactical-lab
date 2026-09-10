# Team Instruction Repair Report

## Catalogue and evidence boundary

`data/team_instruction_catalog.json` records the user-confirmed FM26 UI
identity only: 18 IP categories and 9 OOP categories.  A selectable value is
registered only when it was visible as the current screenshot value.  Every
category and value has `analysis_status: effect_not_modelled`; category/value
identity is not evidence of a tactical effect.

`data/team_instruction_evidence.json` is a dedicated instruction UI evidence
registry.  It is intentionally separate from role behaviour evidence.  The
two evidence records retain `user_ingame_capture` / `user_ingame_verified`
provenance for the IP and OOP screenshots.

## Verified current values

IP: passing directness standard, high tempo, less frequent time wasting,
continuous attacking transition, standard attacking width, balanced
creativity, break-press build-up, short goal kicks, centre-back goalkeeper
distribution, balanced attacking involvement/dribbling/progression/passing
style/long shots, standard patience, low crosses, and quick goalkeeper
distribution.

OOP: mid block, standard defensive line, more frequent pressing,
counter-press transition, tackle harder, balanced cross play and pressing
trap, goalkeeper short distribution yes, and higher defensive-line action.

`세트피스 유도` is a verified category whose visible value was truncated.  It
has no selectable value and is rendered as `선택값 검증 필요`.

## Input integration

`core.team_instructions` is a pure validator/normalizer.  It accepts only
catalogue-backed canonical category/value IDs, rejects unknown IDs and phase
mismatches, permits missing categories, and makes no tactical inference.
`core.tactic_normalization` accepts an optional adapter-supplied instruction
catalogue, so the core has no file-path or web dependency.

The web API exposes `GET /api/team-instructions` (optionally `?phase=IP`) and
passes canonical phased instruction input through `POST /api/analyze`.  The
analysis response adds `team_instruction_input_status` with
`effect_not_modelled`; Connectivity and tactical-area results are unchanged.

The web UI renders IP and OOP sections with verified values only, explicit
input/effect status, and the unresolved set-piece category.  A separate
`data/sample_team_instructions_leicester.json` fixture powers the Web
Leicester example without changing the historical golden sample JSON.

## Compatibility and limits

Tactics without `ip_team_instructions` or `oop_team_instructions` remain
valid.  Legacy unphased `team_instructions` remains preserved by the existing
analysis compatibility path.  No role data, role behaviour, semantic, ERS,
Connectivity rule, official role-evidence package, score, or tactical effect
was changed.

## Validation

New tests cover category counts/labels, observed values only, the truncated
set-piece value, validator failures, API contracts, no-effect analysis status,
legacy input, and UI section/status presence.  Full regression results are
recorded in the delivery report for this repair phase.
