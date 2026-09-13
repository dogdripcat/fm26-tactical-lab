# Website MVP Redesign
## Layout and UX

The analysis page now begins with a pitch-centred workspace and a compact
Tactical Snapshot panel. After analysis, the panel shows an integrated summary
and three concise cards: 연결성, 전진성, 지원 구조. Each card opens its
existing detailed section only when requested.

The pitch has a single set of view controls: 기본, 연결, 전진, 지원. The
controls reuse existing structural links and existing evaluator output; they
do not calculate a new tactical conclusion.

## Opponent comparison MVP

The second top-level tab contains an opponent formation selector, a visual
formation preview, and a 구조적 상성 result area. It supports 4-3-3,
4-2-3-1, 4-4-2, 4-1-4-1, 3-4-2-1, 3-5-2, and 3-4-3. Its output is limited to
formation-level structural observations and explicitly avoids win percentages,
deterministic superiority, or role-effect inference.

## Runtime asset fix

The local web server now serves the already-public nested static JavaScript
and data assets through its strict asset map. This lets the browser load the
same static analysis pipeline that the tests exercise.

## Files changed

- web/static/index.html
- web/static/style.css
- web/static/app.js
- web/app.py

## Verification

- Full unittest discovery: 243 tests passed.
- Core self-test: passed.
- JavaScript syntax checks: passed.
- git diff --check: passed.
- Local browser smoke test: analysis workspace loaded; opponent tab rendered
  the selected 4-3-3 preview and structural comparison observations.

## Known limitations

The opponent tab is a formation-structure MVP. It has no opponent roles,
Team Instruction interpretation, player data, match simulation, expected
goals, or win-rate model. Connectivity, Progression, and Support evaluators
remain unchanged. No commit or push was performed.
