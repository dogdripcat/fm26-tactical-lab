# Static Website Conversion Audit

## Current API adapter inventory

| API endpoint | Previous browser use | Python source | Static replacement |
|---|---|---|---|
| `GET /api/health` | Deployment smoke check only | `web.app` | Not required by the static runtime. |
| `GET /api/roles` | Role selector | `web.api.roles_payload` | `role_catalog.json` + `role_behaviours.json` + `role_resolution.js`. |
| `GET /api/presets` | Formation selector | `web.api.FORMATION_PRESETS` | `data/presets.json`. |
| `GET /api/pitch-layout` | Display coordinates | `web.pitch_layout` | `app.js` display-only coordinates; never input to the engine. |
| `GET /api/team-instructions` | Team instruction controls | `core.team_instructions` | `team_instruction_catalog.json` + `team_instructions.js`. |
| `GET /api/sample-team-instructions` | Fixture only | `web.api` | Not needed by normal static use. |
| `GET /api/sample` | Fixture only | `web.api` | Not needed by normal static use. |
| `POST /api/analyze` | Analysis | `core.pipeline`, `connectivity_engine`, `web.analysis_presenter` | `tactic_normalization.js`, `role_resolution.js`, `positional_relationships.js`, `connectivity_engine.js`, `analysis_presenter.js`, `tactic_analysis.js`. |

## Browser runtime

`web/static/index.html` loads module-based JavaScript with relative URLs. `data_loader.js` resolves every JSON URL from its own module location, so the same files work at a GitHub Pages project subpath such as `/fm26-tactical-lab/`.

The static runtime reads only packaged JSON and keeps tactic input in browser memory. It calls no `/api` endpoint, uses no database, and contains no OpenAI API dependency. Python remains in the repository as the reference implementation and regression oracle.

## Data copies

The deployment copies under `web/static/data/` are read-only publication copies of the existing verified source JSON. This conversion does not alter role identities, evidence, abbreviations, role behaviours, semantic vocabulary, ERS ontology, constraints, or team instruction evidence.

## Parity method

`test_static_website_conversion.py` invokes `web/static/js/parity_runner.mjs`, then compares normalized nodes, edges, provenance, progression chains, isolated nodes, evidence-completeness summaries, and presentation output with the Python connectivity engine and presenter. Fixtures cover Leicester 4-2-3-1, 4-3-3, 4-4-2, and 3-4-2-1 with dedicated left/right Wing-Back positions.

## Deployment preparation

`.github/workflows/pages.yml` packages `web/static` for GitHub Pages. It has not run or deployed a site in this phase. The existing Python/Render files remain only as reference/development infrastructure and are not used by the static public runtime.
