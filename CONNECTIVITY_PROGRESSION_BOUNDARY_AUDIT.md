# Connectivity ↔ Progression Boundary Audit

## 1. Connectivity definition

Connectivity v2 asks whether configured IP positions form a structural graph that can connect occupied lines and expose a complete route to the forward band. It owns graph existence, route existence, regional structural availability, alternative structural routes, node-removal survival, and support/recycle availability. It is position-first, score-free, and does not model observed passes.

The existing field name `progression_routes` is historical structural terminology: it means a directed **complete Connectivity route** from a start node to the configured forward band. It does not yet mean that the route has been evaluated for progression quality, line gain, tactical destination quality, or performance.

## 2. Progression definition

Future Progression asks how a candidate route advances through meaningful tactical space: its occupied-line gains, skips, advancement sequence, reachable tactical line, regional movement, and whether it advances then has no further advanced outlet. It reuses the frozen Connectivity graph and never recreates graph existence or treats raw route count as quality.

Progression may say “수비선에서 중원을 거쳐 전방까지 단계적으로 전진할 수 있습니다.” It may not say that the route produces a chance, penetrates a block, or predicts a successful pass.

## 3. Overlap risks

The word “progression” currently appears in `forward_progression`, `diagonal_progression`, `progression_routes`, regional route labels, and connector dependency. Reusing those facts as a separate evaluator without a boundary would duplicate Connectivity or turn a structural route count into a qualitative grade.

The boundary is therefore: Connectivity establishes whether the candidate structure exists; Progression describes the advancement characteristics of that existing structure. Neither output may silently overwrite the other.

## 4. Ownership matrix

| Current item | Classification | Owner/reuse reason |
| --- | --- | --- |
| `structural_links` | B. shared primitive | Connectivity creates and owns them; Progression may consume their configured bands, direction, lanes, and provenance read-only. |
| `forward_progression` / `diagonal_progression` | A with B fields | They remain frozen Connectivity link relations. Their forward direction can seed a future advancement event, but relation names are not a Progression conclusion. |
| `same_line_support` / `recycle` | A with B context | Connectivity owns fallback structure. Progression may record them as context before/after advancement, never as direct advancement. |
| `progression_routes` | A with B candidate input | Connectivity owns complete structural route existence; Progression profiles existing distinct route families only. |
| display `route_families` / `display_plan` | A / D | Display priority is UI-only; representative IDs may help highlight a precomputed profile, but must not determine the evaluation. |
| `network_regions` | A with B eligibility | Connectivity owns whether a complete regional route exists. Progression may inspect advancement properties of eligible regional route families. |
| `line_continuity` | A | Connectivity owns whether adjacent occupied lines are connected. Progression may cite it, but must not recalculate or relabel it as quality. |
| route survival / `connector_dependency` | A with B comparison input | Connectivity owns survival of complete structural connectivity. Progression dependency requires a separate property-specific removal test. |
| `support_recycle` | A with B context | Connectivity owns fallback availability; Progression must not call it advancement or retention quality. |
| `role_adjustments` | B. verified modifier context | Read-only role-evidence annotations may qualify a Progression description, but may never create/delete baseline links. |
| `structural_basis`, `absolute_band_delta`, adjacency provenance | D and B | Debug/provenance today; vertical bands and occupied indexes are reusable primitives, while display classes and raw counts are not. |

## 5. Connectivity outputs reusable by Progression

| Connectivity output | Permitted Progression use | Forbidden use |
| --- | --- | --- |
| nodes with `vertical_band`, `vertical_index`, `lateral_slot` | Build a read-only route profile against configured tactical ontology. | CSS or pitch-coordinate calculation. |
| directed structural links | Identify candidate sequence edges and their direction. | Generate missing links or infer pass completion. |
| complete routes and evaluator route families | Deduplicate candidate profiles and choose explainable examples. | Recompute complete Connectivity route existence. |
| regional Connectivity | Limit regional analysis to regions with candidate routes. | Claim regional advancement quality merely from route count. |
| support/recycle | Describe pre-advance/later fallback context. | Claim press resistance, retention, or safety. |
| Connectivity dependencies | Compare with a later Progression-specific result. | Inherit the dependency label unchanged. |
| role adjustments | Attach verified context and evidence IDs. | Upgrade absent evidence into a negative result. |

## 6. Advancement-event definition

An **advancement event** is a directed existing structural link whose source and target have known configured vertical indexes, whose direction is `forward`, and whose target lies on a more advanced occupied tactical line than its source.

Canonical `vertical_band` supplies the human-readable origin/destination labels. The ordered occupied-line sequence of the actual tactic supplies relative advancement. This dual rule keeps the semantic distinction between defence, midfield, attacking midfield, and forward without penalising a formation for absent canonical bands.

`forward_progression` and `diagonal_progression` in the frozen engine qualify only when their actual link direction remains `forward`. They are both advancement candidates; diagonal movement is not disqualified merely for moving laterally as well. `same_line_support` and `recycle` are not direct advancement events.

## 7. Occupied-line gain definition

For a tactic, sort the distinct configured `vertical_index` values into its ordered occupied-line sequence. A forward link has:

- `no_line_gain`: same-line support or recycle, or no safe band information;
- `one_occupied_line_gain`: source and target are neighbouring elements of that sequence;
- `multiple_occupied_line_gain`: target is later than the next occupied line.

This is descriptive, not a score. In a 4-4-2, `defensive_line(1) → midfield(4)` is one occupied-line gain because 1 and 4 are consecutive occupied lines. It is not treated as a multi-line jump merely because two canonical classifications are absent.

## 8. Line-skip definition

A **line skip** exists only where at least one other occupied vertical index lies strictly between an existing forward link’s source and target indexes. It is evaluated against the tactic’s occupied-line sequence, not canonical numeric distance.

Thus `CB → AM` can be a line skip when a DM/CM line is configured between them. `CB → CM` in a 4-4-2 is not a skip when defence and midfield are neighbouring occupied lines. This definition preserves the occupied-line adjacency repair and avoids formation-specific penalties.

## 9. Progression-sequence definition

A future **progression sequence** is a bounded, ordered explanation over existing Connectivity links. It may contain support or lateral context before a forward advancement event, followed by one or more advancement events. Its question is whether the sequence reaches a later occupied line, not whether the graph exists.

Production Progression must consume frozen topology and existing route families. It must not run a second independent connectivity traversal to create a different definition of complete route existence.

## 10. Route-progression-profile definition

Each deduplicated Connectivity route family may receive a read-only profile:

```json
{
  "route_family_id": "...",
  "origin_band": "defensive_line",
  "destination_band": "forward",
  "occupied_line_gains": [],
  "skipped_occupied_lines": [],
  "advancement_events": [],
  "lateral_transfers_before_advance": [],
  "dominant_region": "left",
  "final_region": "left",
  "reaches_forward_band": true,
  "reaches_attacking_midfield": false,
  "reaches_advanced_wide_zone": "unknown",
  "role_adjustment_notes": [],
  "limitations": []
}
```

It records configured structural facts and evidence-backed role notes. It has no score, rate, quality adjective, or predicted outcome.

## 11. Regional advancement

Connectivity answers whether a region has a complete structural route. Progression may instead describe: which region contains an advancement event, the highest configured band it reaches, whether it transfers between lanes before advancing, and whether it depends on another region before its first advancement.

It must not equate a `left`, `centre`, or `right` route count with better advancement. A region with no complete Connectivity route remains a Connectivity fact, not a Progression failure grade.

## 12. Central, half-space, and wide limitations

The configured-position registry safely exposes only `left`, `centre`, and `right` lateral slots. They are not a global half-space or wide-channel ontology. Display coordinates are UI-only and may not fill this gap.

Verified ERS/semantic items can add role-scoped context only: `move_into_halfspace` may be recorded for the verified role; `move_inside` does not establish a fixed central or half-space destination; `use_wide_flank` is not a generic configured-wide-zone proof. Therefore baseline Progression must report half-space/wide destination as `unknown` unless the relevant verified ERS item directly supplies it.

## 13. Advance-then-stall definition

`advance_then_stall` is a route-prefix condition: a reachable configured structure has at least one advancement event into a non-forward occupied line, but from the receiving node/set there is no remaining existing forward path to any later occupied line or forward-band endpoint.

It differs from no Connectivity because the initial advancement exists. It differs from Connectivity’s cautious `dead_ends` output because that output protects against false positives and has its own central-relay conditions. Progression may report the stalled advancement context without declaring a player isolated or the tactic weak.

## 14. Progression dependency definition

Progression dependency is not inherited from `connector_dependency`. It is a separate future node-removal comparison: remove an eligible intermediary from the same frozen graph and check whether a **Progression-specific property** disappears, such as all access to the forward band through the centre, every profile with a line skip, or every profile reaching a particular advanced region.

A node can be unnecessary for complete Connectivity but still be the only route to a specific advanced destination. Conversely, a Connectivity bridge need not be uniquely required for a Progression property. Both results must retain their separate labels and limitations.

## 15. Role-semantic relevance

| Verified semantic | Progression relevance | Boundary |
| --- | --- | --- |
| `send_forward` | Direct progression modifier | Can annotate an existing source advancement event; cannot create it or assert success. |
| `advance_to_attacking_midfield` | Destination/movement modifier | Can annotate verified expected movement toward an AM band; no baseline node move. |
| `move_into_halfspace` | Movement context only | Role-scoped ERS context; does not infer a universal half-space route. |
| `move_inside` | Movement context only | Explicitly has no fixed destination target. |
| `receive_between_lines` | Destination/reception modifier | May annotate a verified receiving context; does not establish a line gain by itself. |
| `receive_centrally` | Destination/reception modifier | Does not create an advanced central route. |
| `attack_space_in_behind` | Insufficient for structural Progression | Movement/penetration-adjacent context, not a receiving or passing event. |
| `move_to_receive` | Movement context only | Does not prove actual receipt or distribution. |

No unverified behaviour, player attribute, or player instruction becomes a modifier.

## 16. Configured Position / ERS boundary

Configured Position remains the baseline starting location and the only source of Connectivity topology. Expected Role Space remains a verified expected occupation, reception, movement, or structural-effect annotation.

Future Progression may provide two parallel descriptions: **base progression** from configured positions and **role-adjusted progression interpretation** from verified ERS. It may not merge expected space into the baseline graph, move nodes, or replace a configured route with a role claim.

## 17. Synthetic-case design results

The following are future pure-topology fixtures, not production evaluation results.

| Case | Required distinction |
| --- | --- |
| A. connected but no advancement | Support/recycle graph exists; no forward link to a later occupied line. |
| B. steady staged advancement | Every forward edge is one occupied-line gain. |
| C. legal occupied-line skip | An existing forward edge bypasses a configured occupied line. |
| D. apparent canonical skip only | Sparse 4-4-2-style defence→midfield is one occupied-line gain, not a skip. |
| E. wide-only advancement | Advancement events occur through a left/right lane; no central advanced profile. |
| F. central-only advancement | Centre profile exists; no wide advancement conclusion. |
| G. lateral before central advancement | Support/lateral context precedes a centre advancement event. |
| H. advancement to midfield then stall | Initial line gain exists but no later forward continuation. |
| I. many Connectivity routes, same profile | Deduplication prevents raw-route inflation. |
| J. fewer routes, two profiles | Distinct sequences/destinations are retained without ranking. |

## 18. Seven-preset observations

All observations are read-only from the frozen position-only topology. They are not formation rankings.

| Preset | Occupied tactical lines | Safe Progression observation |
| --- | --- | --- |
| 4-2-3-1 | 0, 1, 3, 5, 6 | Complete candidates can be described as staged occupied-line advancement to forward. |
| 4-3-3 | 0, 1, 3, 4, 5, 6 | Candidate families include both staged and potential occupied-line-skip sequences; future profiles must deduplicate before any diversity description. |
| 4-4-2 | 0, 1, 4, 6 | Defence→midfield is a valid one-occupied-line gain despite missing DM/AM bands. |
| 4-2-4 | 0, 1, 4, 5, 6 | Candidate families can differ between staged midfield→AM→forward movement and a potential occupied-line skip; neither is ranked. |
| 3-4-2-1 | 0, 1, 2, 4, 5, 6 | Wing-back and central lines create candidate staged or skip profiles; configured positions, not display geometry, determine the classification. |
| 3-4-3 | 0, 1, 2, 4, 5, 6 | Same occupied-line method applies; route quantity is not advancement quality. |
| 3-5-2 | 0, 1, 2, 4, 6 | Sparse canonical gaps are treated through consecutive occupied lines, not as automatic skips. |

The current complete-route totals remain 16, 48, 32, 32, 25, 20, and 40 respectively. They are provenance counts only and must not appear as a Progression quality scale.

## 19. Boundaries with future dimensions

| Dimension | Primary question | Boundary from Progression |
| --- | --- | --- |
| Connectivity | Can configured structure connect relevant positions/lines? | Supplies the graph and route existence. |
| Progression | How does an existing structure advance through configured tactical space? | No chance or threat conclusion. |
| Penetration | Does advanced access/movement threaten or disrupt the defensive block? | `attack_space_in_behind` alone remains outside structural Progression. |
| Chance Creation | Does structure create a chance for a teammate? | Advanced destination is not chance quality. |
| Goal Threat | Do roles/players threaten scoring positions? | Reaching forward band is not goal threat. |
| Support | Are supportive options usable around the ball? | Existing fallback context is retained; execution and retention are out of scope. |
| Partnerships | How do specific roles/players combine? | No synergy or conflict inference from route co-occurrence. |

## 20. Proposed Progression schema

```json
{
  "progression_evaluation": {
    "advancement_continuity": {},
    "line_gains": {},
    "line_skips": [],
    "highest_reachable_line": {},
    "regional_advancement": {"left": {}, "centre": {}, "right": {}},
    "route_profiles": [],
    "advancement_diversity": {},
    "progression_dependency": [],
    "advance_then_stall": [],
    "role_adjustments": [],
    "observations": [],
    "limitations": []
  }
}
```

All statuses must preserve input node/edge IDs, configured band facts, and evidence IDs for role notes. The schema intentionally has no score, grade, probability, performance estimate, or UI prescription.

## 21. Recommended implementation order

1. Create pure, isolated fixture tests for occupied-line gains and skips, including the sparse 4-4-2 rule.
2. Create a read-only route-profile builder that accepts frozen Connectivity v2 output.
3. Add advance-then-stall and Progression-specific dependency only after profile invariants pass.
4. Add a separate evaluator output in parallel with Connectivity; retain exact v2 regression output.
5. Design user language after evaluator fixtures, not before.

## 22. Items that must remain unimplemented

- Production Progression evaluator or UI in this audit phase.
- Any change to frozen Connectivity topology, evaluator rules, display priority, or semantics.
- Scores, grades, weights, percentages, or rankings.
- Player attributes and execution quality.
- Team Instruction tactical effects.
- Penetration, Chance Creation, Goal Threat, Partnerships, and performance prediction.
- Role-name inference, unverified behaviour promotion, or ERS-driven baseline-link creation.

## 23. Files inspected

- `connectivity_engine_v2.py`
- `connectivity_qualitative_evaluator.py`
- `web/static/js/connectivity_engine_v2.js`
- `web/static/js/connectivity_qualitative_evaluator.js`
- `web/static/js/connectivity_evaluation_presenter.js`
- `positional_relationships.py`
- `configured_position_registry.json`
- `expected_role_space_ontology.json`
- `connectivity_semantic_vocabulary.json`
- `role_behaviours.json`
- Connectivity v2 design, occupied-line repair, progression audit, and baseline reports
- Connectivity v2 evaluator and presenter tests

## 24. Git status

Baseline inspected: `0a78ac98bb52c054b0edc2c9eb893beeffa1bcb5`.

This audit adds only `CONNECTIVITY_PROGRESSION_BOUNDARY_AUDIT.md`. It does not modify production Connectivity, role data, tests, UI, or evaluator behaviour. No commit or push is performed.