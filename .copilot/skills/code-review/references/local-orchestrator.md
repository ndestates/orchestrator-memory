# Local orchestrator install — review checks

**Product direction (2026-07):** apps install and upgrade the template **per-app** via the versioned CLI. Fleet multi-app **wave** is deprecated and must not return.

## Commands (expected)

| Action | Expected |
|--------|----------|
| Install / bootstrap | `orchestrator init <app>` or documented registry install |
| Upgrade | `orchestrator upgrade <app>` (explicit path; no silent fleet) |
| Check version | `orchestrator check` / `session-orchestrator-check.py` |
| Uninstall | dry-run default; apply needs `--apply` and project delete needs `--yes` |

## Blocking if the diff…

- Reintroduces fleet wave deploy entrypoints (`scripts/*wave*`, `orchestrator wave` without hard removal plan)
- Documents multi-app unattended deploy as the default path
- Adds destructive uninstall/install without dry-run default
- Removes protected app paths (`.git`, `app/`, `.env*`, business source) from safety lists
- Touches high-risk stamped files without regenerating `reports/security/bundle-hashes.json` (or equivalent CI stamp)
- Commits secrets, live credentials, or real PII in examples

## High priority

- Deploy-bundle selections still match INSTALL.md / per-app-upgrade docs
- `docs/internal/` not published to npm package `files`
- Template refuses uninstall of monorepo source unless force flag
- Version single source of truth remains `VERSION`

## Important

- Resume/session skills still cache-first
- Chains that say “wave” only in historical changelog context

## Out of scope for this lens

App business domain logic — use stack PHP/MySQL/Python lens instead.
