# Documentation complete: installation + licensing

**Date:** 2026-07-09  
**Branch:** `feature/installer-docs-cease-wave-2026-07-09`  
**Chain used:** documentation-specialist (single skill path; outline-first) — not full documentation-full scan

## Human site

| Page | Status |
|------|--------|
| `docs/getting-started/installation.md` | **new** — bash, PowerShell, pip, per-app CLI, wave ceased |
| `docs/reference/licensing.md` | **new** — env vars, verify, fail-open, MCP note |
| `docs/index.md`, getting-started/reference/guides indexes | refreshed |
| `docs/guides/template-deploy.md`, `wave-deploy-log.md` | refreshed — per-app default |
| `docs/TEMPLATE_ADOPTION.md`, root `INSTALL.md`, `README.md` | refreshed |
| Outline | `reports/docs/.doc-outline-2026-07-09.md` |

## Agent cache

- `docs/codebase/README.md`, `CONCERNS.md` (§9 mitigated + §11 license), `INTEGRATIONS.md`

## Installer artifacts

- `scripts/install.sh` — `--cli` for `pip install -e .`
- `scripts/install.ps1` — Windows PowerShell bootstrap + `-Cli`
- Existing: `src/orchestrator_cli` init/upgrade/license; wave fail-closed policy

## Content policy

- pass (placeholders only for license URL/key; no secrets/tips)

## Verify

- `bash scripts/install.sh` — OK
- `python3 scripts/docs-link-audit.py` — all internal links OK
- Wave CLI without approval — BLOCKED

## Gaps

1. Live license server URL for production still placeholder (`licenses.example.com`)
2. pytest not pre-installed on this host at doc time — install via `pip install -e ".[dev]"` before CI parity
3. Full `/read-codebase` scan not re-run (refresh scope)

## Next

1. Commit + PR this branch (includes stop-wave lineage)
2. Merge PR #115 / this branch to develop
3. Use only per-app `orchestrator upgrade` for app updates
