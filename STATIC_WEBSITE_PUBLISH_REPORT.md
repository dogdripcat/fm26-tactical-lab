# FM26 Tactical Lab Static Website Publish — Phase 2

## Pre-publish verification

- Python unittest discovery: 191 passed.
- `fm26lab.py self-test`: passed.
- JavaScript syntax checks: passed.
- Python-to-JavaScript static parity: Leicester 4-2-3-1, 4-3-3, 4-4-2, and 3-4-2-1 passed.
- `git diff --check`: passed after removal of one trailing blank line in the parity test file.

Leicester remains 11/11 resolved roles, 61 edges, 2 semantic-complete edges, 7 mixed edges, 4 compatibility-only edges, 48 evidence-missing edges, 6 unknown chains, and 0 isolated nodes.

## Static artifact

The GitHub Pages workflow packages `web/static` directly. The artifact root contains `index.html`, `style.css`, `app.js`, `js/`, and `data/`.

`data/` includes the role catalogue, configured-position registry, role behaviours, semantic vocabulary, ERS ontology, team-instruction catalogue/evidence, role aliases, and all seven formation presets used by the browser runtime.

## Runtime and privacy

All normal analysis runs in browser memory. Published JavaScript uses relative static URLs and does not require `/api/`, `localhost`, Render, a database, an API key, or a Python process. The expected GitHub Pages project subpath is supported through `./` asset references and module-relative JSON URLs.

Python remains a local reference and regression implementation only. Render remains historical/development infrastructure and is not part of the public deployment path.

## Secret audit

The staged public artifact was checked for private keys, API keys, GitHub tokens, passwords, credentials, `.env` files, and personal filesystem paths. No actual secret or personal path was included. The only `token` text matched the GitHub Actions `id-token` permission and ordinary JavaScript variable names.

## Publish result

- Static conversion commit: `9fb1a89b1b0937d44f6ca60c9b8880b9335ed01b`.
- Commit message: `Convert FM26 Tactical Lab to static browser app`.
- Push: `origin/main` advanced from `083baf2` to `9fb1a89` without force push.
- Workflow: `.github/workflows/pages.yml` uses `actions/checkout`, `actions/configure-pages`, `actions/upload-pages-artifact` with `path: web/static`, and `actions/deploy-pages`.

The local GitHub CLI was not installed, and an unauthenticated workflow-page fetch was unavailable, so workflow completion could not be observed from this environment. GitHub Pages has not been claimed as live here.

## Required GitHub setting

In the repository, open **Settings → Pages** and set **Source** to **GitHub Actions**. After the workflow succeeds, the expected URL is:

`https://dogdripcat.github.io/fm26-tactical-lab/`

## Product logic

No role data, configured-position data, role behaviour, semantic vocabulary, ERS, Connectivity/progression logic, team-instruction catalogue, evidence, formation preset, pitch coordinate, or presentation meaning changed during publish.
