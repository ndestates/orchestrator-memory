# Generic Laravel wave app — CI/CD specialization

Applies to Laravel apps unless a dedicated `*-ci.md` exists.

## Expected workflows

| Workflow | Typical trigger |
|----------|-----------------|
| `chain-audit.yml` | PR/push `develop`, `feature/**` |
| `loop-daily-triage.yml` / `loop-weekly-watch.yml` | Schedule / dispatch |
| `run-chain.yml` | `workflow_dispatch` |

Many Laravel apps **lack** a full `ci.yml` in Actions — tests run in DDEV locally.

## Pre-push gate

```bash
ddev start
ddev exec php artisan test    # or pest/phpunit per TESTING.md
bash scripts/chain-audit.sh   # when chains touched
```

## BLOCKED when

- Application PHP changed but no local test run documented
- Filament/auth changes without `auth-stability-guards` or project guard script when present
- Deploy workflows would trigger on feature branch (readiness script shows unexpected deploy in `triggers_on_push`)