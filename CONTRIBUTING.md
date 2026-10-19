# Contributing

> Primary source: [ClientRequirement.md](ClientRequirement.md) · Phases & quality gates: [PRD.md](PRD.md) §7

Thanks for contributing to LabelForge. This is a prototype codebase — keep changes focused, working, and covered by the existing gates.

## Getting started

1. Follow the setup for your surface in [README.md](README.md#run) (local API + UI, Docker, or Streamlit).
2. Python deps install from `app/pyproject.toml`: `pip install -e "app[dev]"`.
3. UI deps install from `app/ui`: `npm ci`.

## Quality gates (must pass before a PR)

Run from `app/` unless noted:

| Gate | Command |
|------|---------|
| Unit tests | `pytest tests/` (28 tests) |
| Golden evals (CI regression gate) | `python evals/runners/run_eval_suite.py` (30 golden fixtures) |
| Lint | `ruff check src tests` |
| Format check | `ruff format --check src tests` |
| UI type-check + build | `cd ui && npm run build` |
| Factory graph smoke | `USE_FACTORY_GRAPH=true pytest tests/ -q` |
| RAG smoke | `RAG_ENABLED=true pytest tests/ -q` |

CI runs all of the above on every push/PR, plus `pip-audit`, `npm audit`, and `gitleaks`.

## Style & conventions

- **Python:** 3.11+, type-hints, ruff-formatted; module headers per [CODE_COMMENT_HEADER_TEMPLATE.md](CODE_COMMENT_HEADER_TEMPLATE.md) (PRD §7.5) on production modules.
- **TypeScript/React:** `tsc -b` must be clean; USWDS-aligned tokens live in `ui/src/styles.css`.
- **Domain language:** use "verify/verification", not "check".
- **No real brand assets.** All fixtures are synthetic (fictional brands).

## Pull requests

1. One focused change per PR; describe the requirement it serves.
2. Note any trade-offs or limitations in the PR description (evaluation criterion: "document trade-offs").
3. Do not remove or bypass existing features, eval fixtures, or CI gates — extend them instead.

## Questions

Open a discussion issue, or see [APPROACH.md](APPROACH.md) for architecture and design decisions.
