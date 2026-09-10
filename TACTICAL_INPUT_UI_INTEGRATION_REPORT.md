# Tactical Input UI Integration Report

## Flow audit and result

Before this repair, the web UI had IP formation and role editing plus separate
IP/OOP instruction panels, but a formation change rebuilt the whole tactic
object.  This discarded instruction state and did not explicitly validate a
role against its configured position before analysis.

The current flow is: select IP formation, inspect configured-position nodes,
select an IP role at each node, set IP/OOP team instructions, then analyze IP
Connectivity.  The header and instruction panel explicitly distinguish IP
structure/role editing from OOP team-instruction input; OOP formation and role
editing remains limited.

## Phase-aware state and compatibility

The frontend exposes phase-aware access through `phaseState(phase)`:
formation, configured positions, roles, team instructions, and editing status
are grouped by phase.  Its `analyzePayload()` adapter preserves the established
backend fields (`ip_formation`, `ip_roles`, `ip_team_instructions`,
`oop_roles`, and `oop_team_instructions`) rather than forcing a breaking
migration.

The additive `tactic_input` response field returns supplied IP/OOP state
separately.  Existing top-level `connectivity`, `areas`, and
`team_instruction_input_status` remain unchanged.

Example request:

```json
{
  "name": "My tactic",
  "ip_formation": "4-2-3-1",
  "ip_roles": {"GK": "BPGK", "ST": "CF"},
  "ip_team_instructions": {"tempo": "tempo_high"},
  "oop_roles": {},
  "oop_team_instructions": {"pressing_line": "pressing_line_mid_block"}
}
```

IP role entries must cover the selected web formation and resolve to a role
available at that configured position.  Missing/invalid IP role input is a
hard error.  Missing instruction categories are permitted.  Effect-not-modelled
team instructions and limited OOP structure editing are warnings, not errors.

## Formation, roles, sample, and instructions

When IP formation changes, removed positions disappear, new positions remain
unselected, and an existing role survives only when it is still selectable at
the retained configured position.  No replacement role is guessed.  IP and OOP
instruction maps survive this change.

The Web Leicester loader merges `sample_leicester_4231.json` with the separate
`sample_team_instructions_leicester.json` fixture deterministically.  This
does not alter the historical golden sample file or Connectivity input.

Nodes display configured position, selected verified identity label/abbreviation
when available, and behaviour evidence coverage.  The selector never invents
an abbreviation.  The instruction UI states that it shows confirmed values
only, and leaves the truncated set-piece value unavailable.

## Analysis scope and responsive UI

The result UI describes Connectivity as IP-directed edges.  OOP instruction
input does not imply OOP Connectivity analysis.  The analysis status text and
limitations explain that team instruction effects are not modelled, OOP
analysis is limited, Unknown is not bad, and Connected is not a quality score.
Existing grid layout retains its mobile media rule; instruction sections are
separate DOM sections and do not overlay the pitch.

## Scope preserved

No role behaviours, semantic vocabulary, ERS, Compatibility rules, edge state
logic, progression chains, scores, or team-instruction tactical effects changed.
No official role evidence package was applied.  Git commit, push, and deploy
were not performed.
