# Tactical UI Visual Hotfix Report

## Coordinate root cause and correction

The former client used one global coordinate table.  `ST` was set to x=42 so
it could appear alongside `CF` in a two-forward view; that same value also
applied to the single-forward 4-2-3-1, placing ST left of AMC.

`web.pitch_layout` now creates display-only coordinates from each formation's
configured positions.  A lone `ST` or `CF` is x=50; a two-forward pair is
placed symmetrically at x=42 and x=58.  GK, DC, DM, MC, and AMC use the same
central axis when present.  Named left/right pairs are symmetric and all seven
formation layouts are bounded in the pitch.  This module is not imported by
positional relationship or Connectivity code.

## Football pitch and page layout

The previous repeating field grid was replaced by subtle horizontal mowing
stripes and visual-only SVG markings: outer boundary, halfway line, centre
circle and spot, two penalty areas, two goal areas, penalty spots/arcs, and
goal outlines.  The vertical pitch remains bottom-to-top: goalkeeper at the
bottom and attack at the top.

The workspace now places the pitch before secondary input.  A compact toolbar
is followed directly by the pitch; the right inspector contains selected player
details, evidence range, collapsible team instructions, and Connectivity
details.  This keeps the 27 instruction categories out of the initial pitch
viewport.

Nodes are compact position/role cards.  Longer identity and evidence detail
stays in the player/role inspector.  The UI is Korean-first, labels
Connectivity explicitly as IP, and states OOP editing limits and analytical
limitations in one place.

## Responsive and accessibility

The new original dark football-management theme uses custom properties,
consistent controls, focus outlines, text labels alongside edge colours, and a
desktop-first main/inspector grid.  At narrower widths it stacks the inspector
under the pitch and stacks instruction phase panels, without overlaying the
pitch.

## Scope and validation

No role catalogue, configured-position identity, team-instruction catalogue,
role behaviour, semantic, ERS, Connectivity logic, edge state, progression
logic, scoring, or tactical API semantics changed.  The only API addition is a
read-only display-only pitch-layout endpoint.

Tests cover the 4-2-3-1 central spine, left/right symmetry, all-preset bounds,
3-back wing-back coordinates, and required football markings.  Full unittest,
self-test, web tests, JavaScript syntax validation, and the Leicester golden
regression passed for this hotfix.  Git commit, push, and deploy were not run.
