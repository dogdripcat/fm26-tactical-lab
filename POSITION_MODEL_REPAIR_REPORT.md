# Configured Position Model Repair — Phase 1

## Before

- `configured_position_registry.json` had 27 IDs but no `wing_back` position family.
- All three 3-back Web presets used `ML` and `MR`, which are `wide_midfield` positions.
- `LB` and `RB` worked around that absence by selecting both Full-Back and Wing-Back role families.
- There was no explicit canonical-position versus legacy-input alias layer.

## After

The registry is now schema `2.0`. It records three layers:

1. Canonical configured position IDs (`canonical_position_ids`).
2. Explicit legacy input aliases (`legacy_input_aliases`).
3. UI metadata on position entries. The two new Wing-Back entries have `display_family: Wing-Back`, while their `game_abbreviation` is `null` and `abbreviation_verification` is `unverified`.

New internal canonical identities:

- `wing_back_left`
- `wing_back_right`

They are project-internal IDs, not asserted FM26 UI abbreviations.

## Alias policy

Resolved aliases: `DL → LB`, `DR → RB`, `D(C) → DC`, `CM → MC`, `WL → ML`, `WR → MR`.

`CB` remains `unresolved`: its old registry geometry had `lateral_slot: unknown`, so the repair does not silently turn it into `DC`. Unknown or unresolved aliases fail closed. `normalize_configured_position()` in `positional_relationships.py` is the only position-alias resolver used by Web and Connectivity consumers.

## Geometry

`wing_back_left` and `wing_back_right` are in a new deterministic `wing_back_line` (index 2), between the defensive line and defensive midfield. Their lateral slots are respectively `left` and `right`. These geometry facts only produce configured-position relations; they do not create connectivity edges or tactical semantics.

## Preset repair

| Preset | Before wide nodes | After wide nodes | Midfield repair |
|---|---|---|---|
| 3-4-2-1 | `ML`, `MR` | `wing_back_left`, `wing_back_right` | `MCL`, `MCR` |
| 3-4-3 | `ML`, `MR` | `wing_back_left`, `wing_back_right` | `MCL`, `MCR` |
| 3-5-2 | `ML`, `MR` | `wing_back_left`, `wing_back_right` | `MCL`, `MC`, `MCR` |

The back three are now `LCB`, `DC`, `RCB`. The 4-back presets retain `LB`/`RB`; their role availability remains governed by catalog `available_starting_positions` rather than role-family-name matching.

## Selector impact

- Wing-Back configured positions use only catalog starting-position `Wing-Back`.
- Wide Midfield positions use only `Wide Midfield`.
- Full-Back positions use only `Full-Back`, while roles such as Wing-Back remain selectable there when the catalog itself lists `Full-Back` as an available starting position.
- The selector no longer forces `role_families` to equal configured-position family.

## Backward compatibility

Legacy aliases listed above normalize before geometry/Connectivity use. The Leicester 4-2-3-1 sample already uses retained canonical IDs, so its input and connectivity regression remain unchanged. Unresolved `CB` is not guessed.

## Validation

- Dedicated Wing-Back registration, family separation, non-invented abbreviations, 3-back preset use, selector separation, Full-Back availability preservation, alias failure behavior, and 2CB/3CB constraints are covered by new or updated tests.
- No role catalogue identity, role behaviour, semantic, ERS, compatibility rule, or official evidence package was changed.
