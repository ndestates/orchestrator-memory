# Google Stats — CI/CD specialization

## Workflows

| Workflow | Trigger | Notes |
|----------|---------|-------|
| `hardened-image-build.yml` | See workflow `on:` | Builds campaign/automation image |
| `hardened-image-production.yml` | See workflow `on:` | Production deploy path — **never on feature branch push without review** |
| `chain-audit.yml` | PR/push develop/feature | Registry gate |

## No traditional `ci.yml`

Python/campaign scripts may not run in GitHub Actions on every push. Verify:

1. Which workflow fires for **this branch** (readiness script output)
2. Image build secrets present (names only via `gh secret list`)
3. Local script smoke for changed `scripts/` or campaign code before push

## App-specific skills

Chains may reference `google-stats-ops`, `google-stats-script-expert` — ensure registry entries exist after template deploy.