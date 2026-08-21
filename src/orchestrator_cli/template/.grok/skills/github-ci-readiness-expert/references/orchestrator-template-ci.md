# Orchestrator template — CI/CD specialization

## Workflows

| Workflow | Trigger |
|----------|---------|
| `chain-audit.yml` | PR/push develop/feature |
| `loop-daily-triage.yml` / `loop-weekly-watch.yml` | Scheduled |
| `run-chain.yml` | dispatch |
| `mcp-security.yml` | PR/push touching `mcp-server/**` |
| `template-decontamination.yml` | Template hygiene |

## Pre-push

- `bash scripts/chain-audit.sh` must pass after registry edits
- `python3 scripts/compose-registry.py` when split registry files change
- MCP changes: run `mcp-server` tests locally when `mcp-security.yml` will fire

## Wave deploy

Never run fleet wave from feature branches — `wave-deploy-guard.sh` requires `master` or `develop`.