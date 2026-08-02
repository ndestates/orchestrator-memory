# Lightstone — CI/CD specialization

## Workflows (expect on feature branches)

| Workflow | Trigger | Pre-push relevance |
|----------|---------|-------------------|
| `ci.yml` | PR + push `develop`, `master`, `feature/**`, `fix/**` | **Primary gate** — composer validate, changed PHP lint |
| `chain-audit.yml` | PR/push `develop`, `feature/**` | Registry validation |
| `auth-stability-guards.yml` | PR/push (see file) | Auth regression guards |
| `branch-promotion-prs.yml` | push `feature/**`, `develop` | Creates promotion PRs (not a test gate) |
| `ci-preflight.yml` | `workflow_dispatch` only | Manual billing/runner health — run after org policy changes |
| `codeql.yml` | PR schedule | Security scan — async |

## CI does NOT run full PHPUnit in Actions

`ci.yml` intentionally omits DDEV/MySQL tests. **Local gate before PR:**

```bash
ddev exec php artisan test   # or project test command from TESTING.md
```

BLOCKED if only static CI is green but local tests were not run for PHP changes.

## Common failure modes

- Changed PHP lint: syntax error in diff vs `origin/master`
- `composer validate` / `composer install` failure on lock mismatch
- Missing `.github/actions/runner-context` if action path broken
- Node 24 pin drift on `actions/checkout@v6`

## Branch policy

- Feature work on `feature/*` → PR to `develop`
- Never draft on `master`