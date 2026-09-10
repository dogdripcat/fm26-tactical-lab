# Tactical UI Phase 4.2 Report

The workspace is now pitch-first: a compact header and toolbar, large left
football pitch, and a right column dedicated to Team Instructions.  The
Leicester example button, persistent player selector, tactical information
panel, connectivity filter panel, raw metric dashboard, and display toggles
are absent.  The sample fixture remains available to tests.

Role selection remains available by clicking a pitch position; this opens a
small local role dropdown.  Node labels use the verified Korean role name,
without inventing an abbreviation.

Existing directional Connectivity edges render directly on the pitch with
arrowheads and state-specific solid/thin/dashed/warning styles.  Clicking an
edge opens a compact provenance-based tooltip; it uses existing semantic,
behaviour, evidence, and completeness fields only.

`web.analysis_presenter` is presentation-only.  It turns existing edge,
progression-chain, isolated-node, and provenance output into Korean bottom
sections for Connectivity, progression, partnership readiness, space/structure
readiness, suggestions, and evidence/limitations.  It adds no score, edge,
role behaviour, team-instruction effect, or tactical inference.

Role catalogue, behaviour, semantic, ERS, evidence, abbreviation, available
starting-position, and team-instruction data are unchanged.  The 4.1 display
coordinate and football-marking guarantees remain covered by tests.  Git
commit, push, and deploy were not performed.
