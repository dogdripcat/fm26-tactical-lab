# Support User-Facing Analysis UI

## UI and presenter architecture

support_evaluation_presenter.js is a presentation-only adapter. It consumes
support_evaluation and selects already-recorded receiver nodes and structural
link IDs for display. It does not call an evaluator, calculate a new route, or
mutate analysis data.

## Section hierarchy

The Support section appears below Progression and keeps the existing tactical
pitch as the only pitch. Its order is: summary, left/centre/right cards, useful
receiving positions, advance-then-support, single-direction observations,
Support isolation, Support dependency, collapsed role context, and collapsed
limitations.

## User wording

Primary continuation directions are displayed only as 전방, 측면, 리사이클.
Inside/outside never appears as an equal direction or a diversity measure.
Terminal forwards are described as 최전방 종착 위치; they are not labelled as
isolated merely because a further forward continuation is absent.

## Regional cards and receiving positions

Each compact left, centre, and right card reports only evaluator-backed
availability of 전방, 측면, 리사이클 continuation plus cross-region context.
The receiving-position list is capped and prioritises advance-then-support,
isolation, single-direction, dependency, and terminal observations.

## Single-direction, isolation, and dependency

Single-direction wording is neutral. Support isolation means a player can
receive but has no structural continuation afterwards. Support dependency
names the affected receiver, the required support node, the lost primary
direction, and whether removal produces Support isolation. It does not reuse
Connectivity dependency wording.

## Advance-then-support and Progression stalls

Advance-then-support begins only after a recorded Progression advancement
event. It reports what primary continuation remains at that receiving point.
It can explain remaining lateral or recycle options after a Progression stall,
but it never changes the stall or relabels it as isolation.

## Interaction

Regional cards and compact observations select only existing support
continuation links. A Support selection highlights its receiver plus relevant
post-reception links; inbound links are not selected as Support by default.
Connectivity, Progression, Support, node selection, link-mode switching,
formation change, role change, reset, and re-analysis clear incompatible
selection state.

## Evidence and limits

Role context is collapsed and explicitly explanatory: it never creates or
removes a structural link. The limit text states that this is a structural
possibility analysis, not pass completion, player ability, opponent pressure,
match-state, or Team Instruction evaluation.

## Responsive presentation

The three regional cards and observation groups collapse to one column below
850px. The pitch remains the primary fixed-aspect interaction surface and the
section uses compact cards rather than tables.

## Regression scope

No Connectivity v2, Progression, or Support evaluator logic changed. The UI
uses existing support_evaluation fields only. Synthetic presenter tests cover
mixed directions, recycle-only, lateral-only, terminal endpoints, non-terminal
isolation, dependency-capable data, and seven preset presentation checks.

## Synthetic and preset checks

The presenter test covers the requested mixed-direction, recycle-only,
lateral-only, single-direction, terminal, non-terminal-isolation, and
dependency boundaries. The seven configured presets are rendered through the
same compact presenter and are not ranked. Terminal attackers have neutral
copy, including the two-striker safety cases.

## Test results

- Full unittest discovery: 242 passed.
- Core self-test: passed.
- Support, Progression, and Support UI focused tests: 17 passed.
- Python and JavaScript Support parity: passed.
- JavaScript syntax checks: passed.
- git diff --check: passed.

## Frozen output checks

Leicester 4-2-3-1 remains at 38 structural links and 16 progression routes.
The Support UI adds no links, routes, evaluation scores, or tactical rules.

## Files changed

- web/static/js/support_evaluation_presenter.js
- web/static/js/support_presentation_runner.mjs
- web/static/app.js
- web/static/index.html
- web/static/style.css
- test_support_user_analysis_ui.py

No commit or push is part of this phase.
