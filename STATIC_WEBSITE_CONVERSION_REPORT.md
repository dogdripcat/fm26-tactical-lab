# FM26 Tactical Lab Static Website Conversion — Phase 1

## Result

The Phase 4.2 interface now has a static browser runtime. Its normal analysis path loads JSON with relative module URLs and runs tactic normalization, role resolution, configured-position relationships, Connectivity, team-instruction validation, and the deterministic presentation locally in the browser.

## API and backend dependencies

No normal static UI operation uses `/api/roles`, `/api/presets`, `/api/team-instructions`, `/api/pitch-layout`, or `/api/analyze`. The Python API, CLI, SQLite adapter, FMF tools, and WSGI application remain unchanged as reference/development tooling. The static runtime uses neither SQLite nor OpenAI credentials.

## Browser modules and data

- `data_loader.js`: relative static JSON loading.
- `tactic_normalization.js`: phase-aware alias and team-instruction input normalization.
- `role_resolution.js`: catalogue-backed role lookup, ambiguity exclusion, and 3-centre-back availability.
- `positional_relationships.js`: configured-position relation facts only.
- `connectivity_engine.js`: directional edges, provenance, evidence completeness, progression chains, and isolation.
- `team_instructions.js`: verified UI input handling without tactical-effect modelling.
- `analysis_presenter.js`: existing deterministic Korean presentation.
- `tactic_analysis.js`: JSON-compatible local analysis pipeline.

Static data in `web/static/data/` packages the current catalogue, behaviour KB, configured-position registry, semantics, ERS ontology, team-instruction catalogue/evidence, role aliases, and seven presets. The copies preserve the original data and provenance unchanged.

## Parity

The parity test compares structural output, not only totals: resolved node identities, source/target edge IDs, path and edge states, provenance methods, semantic/behaviour/evidence IDs, evidence completeness, progression chain states, isolated nodes, and deterministic presentation.

Leicester 4-2-3-1 remains 11/11 resolved roles, 61 edges, semantic-complete 2, mixed 7, compatibility-only 4, evidence-missing 48, six unknown progression chains, and zero isolated nodes.

Fixtures also verify 4-3-3, 4-4-2, and 3-4-2-1. The three-back fixture includes `wing_back_left` and `wing_back_right`, preserving the repaired configured-position model.

## Public deployment preparation

The relative asset URLs are compatible with `https://dogdripcat.github.io/fm26-tactical-lab/`. A GitHub Pages workflow packages only `web/static`; it is prepared but has not been deployed in this phase. No commit or push was made.

## Privacy and current limits

Tactic input and analysis stay in browser memory during normal use. There is no account, database, feedback endpoint, or server-side tactic storage.

The existing evidence limits remain unchanged: analysis has only the verified FM26 role and team-instruction information already in the knowledge base; team-instruction tactical effects remain unmodelled, OOP editing remains limited, and unknown evidence is not interpreted as a negative tactical result.
