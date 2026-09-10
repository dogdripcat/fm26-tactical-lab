# FM26 Tactical Lab runtime manifest

The Web service is stateless for its public request paths. Package these paths and files from the repository root:

- `web/` — HTTP/WSGI adapter, static assets, configuration, version source, pitch display layout, and presentation-only formatter.
- `core/` — tactic normalization and pipeline.
- `fm26lab.py` — imported only for the existing role dictionary and aliases.
- `connectivity_engine.py`, `tactic_analysis.py`, `positional_relationships.py`.
- `role_behaviours.py`, `role_constraints.py`, `role_knowledge_coverage.py`, `role_connectivity_readiness.py`.
- `current_tactic_evidence_sufficiency.py`, `role_evidence_planning.py`, `expected_role_space.py`.
- `roles.json`, `role_catalog.json`, `role_behaviours.json`, `configured_position_registry.json`, `connectivity_semantic_vocabulary.json`, `expected_role_space_ontology.json`.
- `data/team_instruction_catalog.json` and `data/team_instruction_evidence.json` — read-only Team Instruction UI catalogue and provenance.
- `sample_leicester_4231.json`.

The following are not required for public Web request handling: test modules, `__pycache__/`, Windows `.bat` launchers, local SQLite `data/fm26lab.db`, temporary test databases, FMF inspection inputs, and evidence packages staged for manual import. Do not remove source modules that `fm26lab.py` imports unless its Web-facing dictionary/alias boundary is separately refactored and tested.
