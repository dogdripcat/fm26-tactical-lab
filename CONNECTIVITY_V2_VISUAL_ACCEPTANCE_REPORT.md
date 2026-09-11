# Connectivity v2 Visual Acceptance & Freeze Audit

## 1. Acceptance criteria

The audit checks only the presentation of existing Connectivity v2 truth: structural topology, display priority, qualitative evaluator output, and the user-facing presenter. No score, match prediction, compatibility rule, role behaviour, semantic, ERS item, or team-instruction effect was added.

Acceptance requires readable eleven-position pitches, a clear default link view, text that is grounded in evaluator output, state-safe interaction, and unchanged seven-preset topology.

## 2. Seven-preset visual audit

The static UI was rendered for all seven presets. Each produced exactly eleven selectable position nodes, pitch markings, the primary/full controls, and the IP/OOP team-instruction tabs.

| Preset | Structural links | Progression routes | Visual result |
| --- | ---: | ---: | --- |
| 4-2-3-1 | 38 | 16 | Pass |
| 4-3-3 | 40 | 48 | Pass |
| 4-4-2 | 42 | 32 | Pass |
| 4-2-4 | 38 | 32 | Pass |
| 3-4-2-1 | 42 | 25 | Pass |
| 3-4-3 | 38 | 20 | Pass |
| 3-5-2 | 48 | 40 | Pass |

The pitch keeps central GK/ST/AMC alignment where used. Three-back presets retain separate wing-back configured positions and now show them as `좌 윙백` and `우 윙백`, not internal identifiers.

## 3. Primary/full link behaviour

`주요 연결` is the default, and the existing `default_visible` display plan controls the representative view. `전체 연결` switches only `linkMode`; it does not call analysis. Returning to the primary mode restores the filter. Node or region selection may reveal relevant hidden links temporarily without changing the underlying display plan.

## 4. Pitch/text consistency

The presenter consumes only `connectivity_evaluation` and `connectivity_v2`. For the analysed 4-2-3-1 UI, the visible summary stated that left, centre, and right progression routes exist; the evaluator returned complete route families for those same three regions. Its dependency buttons were AMC, DML, and DMR, matching node-removal regional-progression loss recorded by the evaluator.

No UI-side derivation of a tactical conclusion was found.

## 5. Left/centre/right cards

The cards use football-facing wording: `전방 연결 있음`, `복수 경로 있음`, or `완결 경로 미확인`, plus cross-region access. They do not expose raw route counts, graph terms, or a quality score. Card selection reuses the evaluator’s representative route IDs only.

## 6. Dependency interaction

Dependency items highlight the selected configured position and its incident structural links. Region selection is cleared first. The presenter only lists removal cases with regional or total complete-progression loss, so a merely shared connector is not promoted to a dependency.

## 7. Shared/dependency/bottleneck distinction

The audited wording remains separate:

- shared connector: multiple routes may share a position, without a dependency claim;
- dependency: removing the position removes a recorded progression capability;
- structural bottleneck: only the evaluator may provide this stricter result.

The presenter tests verify that these cases never collapse into one label.

## 8. Support/recycle wording

`지원과 순환` says whether structural fallback is available or limited. It does not claim successful retention, press resistance, safe passing, or player execution quality.

## 9. Role-adjustment wording

Role adjustments remain in their own collapsed section and explicitly state that they do not change structural links. The presenter reads evaluator-provided adjustments only; roles with missing evidence receive no penalty and do not create links.

## 10. Synthetic-case visual results

The eight synthetic evaluator scenarios remain covered by regression: one bridge, side isolation, single-midfielder forward access, independent alternatives, many links without a complete path, progression without recycle, wide-only progression, and central progression without a wide outlet. The presenter tests confirm score-free, non-debug wording for every case.

## 11. False-positive checks

Regression confirms that an ST endpoint is not automatically a dead end, a legitimate wide outlet is not automatically isolated, a shared connector is not automatically a dependency or bottleneck, missing role evidence does not weaken baseline structure, and raw/visible link counts are not presented as tactical strength.

## 12. Responsive audit

Actual narrow-width rendering was inspected. The pitch stays inside the viewport and the region-card CSS collapses to one column below 620px. Two visual-only fixes were required and verified:

- Role names now wrap instead of being cut off with an ellipsis.
- Three-back centre-backs use wider display spacing; dedicated wing-backs use Korean display labels.

At desktop width the workspace keeps the pitch and Team Instructions alongside one another; below 850px Team Instructions move beneath the pitch. The IP/OOP tab controls remain reachable.

## 13. Formation/role state-safety audit

Changing formation calls `clear()`, which resets analysis, selected region, and selected node before rendering the new configured positions. Changing a role also clears analysis and therefore stale links, highlights, and conclusions. Baseline topology remains position-based; roles only provide existing modifier evidence.

## 14. Team Instruction regression

Only one instruction phase is visible at a time. Selections are preserved when IP formation changes. The UI explicitly says that team-instruction effects are not analysed, and Connectivity v2 tests confirm they do not alter topology.

## 15. Known limitations

Connectivity describes structural possibilities only. It does not estimate actual pass completion, attributes, pressure, match context, possession, chance volume, pressing success, or formation quality. OOP structure editing remains limited.

## 16. Forward-role blocker

The ST selector remains limited to catalogued, verified identities. Missing forward roles were not guessed or added for UI completeness.

## 17. UI-only repairs

- `web/static/style.css`: role labels wrap within the pitch node instead of truncating.
- `web/static/app.js`: dedicated wing-back labels are Korean display labels, and three-back centre-back display positions are spaced for narrow screens.

These are display-only changes. The engine, evaluator, role catalog, role behaviours, semantics, ERS, compatibility registry, and topology counts were not changed.

## 18. Test results

- Full unittest: 216 passed.
- `python fm26lab.py self-test`: passed.
- Static browser runners: Connectivity v2 and qualitative runner passed for Leicester input.
- JavaScript syntax: passed for app, v2 engine, evaluator, and presenter.
- `git diff --check`: passed.
- Seven-preset structural regression: unchanged, as listed above.

## 19. Files changed

- `web/static/app.js`
- `web/static/style.css`
- `CONNECTIVITY_V2_VISUAL_ACCEPTANCE_REPORT.md`

## 20. Git status

No commit or push was made. The worktree retains pre-existing Connectivity v2 implementation/report changes and the two UI-only audit repairs above. `git diff --check` is clean.

READY_TO_FREEZE