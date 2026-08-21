# Testing

[UPDATED 2026-07-07]

## Overview

This template validates through **registry audits** and **CI workflows**, not an application test suite.

## Before you begin

Run commands from the repository root on the host (Python 3 required).

## Audit scripts

| Script | Pass criteria |
|--------|---------------|
| `bash scripts/chain-audit.sh` | YAML valid; invokes resolve; score 100/100 |
| `bash scripts/loop-audit.sh` | Loop readiness ≥ 80 (full checklist scores /160) |
| `python3 scripts/check_name_alignment.py` | Grok ↔ GitHub ↔ Copilot parity |
| `python3 scripts/sync_grok_to_github_claude.py` | Sync after `.grok/` edits; then `git diff` review |
| `bash scripts/chain-completion-write.sh` | Chain run audit writer (manual smoke after `/chain`) |

Use `/script-not-shell` for new multi-line audit logic — write `scripts/*.py`, do not inline heredocs.

## CI workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `chain-audit.yml` | PR/push to `develop`, `feature/**` | Chain registry validation |
| `loop-daily-triage.yml` | Weekdays 09:00 UTC | L1 triage host snapshot |
| `loop-weekly-watch.yml` | Mon 09:30 UTC / dispatch | Weekly L1 watch host snapshots |
| `run-chain.yml` | workflow_dispatch | Chain dispatch prep (`chain_id` input) |
| `branch-promotion-prs.yml` | Push `feature/**`, `develop` | Draft promotion PRs |
| `tooling-tests.yml` | PR/push | Root pytest harness + `chain-audit.sh` |
| `mcp-security.yml` | PR/push `mcp-server/**` | MCP sandbox/auth tests |

## Beta readiness

Run `.github/prompts/beta-ready-checklist.prompt.md` before wider template adoption.

## Verify

```bash
bash scripts/chain-audit.sh && python3 scripts/check_name_alignment.py
bash scripts/loop-audit.sh
python3 scripts/docs-link-audit.py
```

All pass before merging doc or registry changes. The docs link audit is now a persisted part of the verification process.

## Next steps

- [Delivery](delivery.md)
- [Chains and skills](../guides/chains-and-skills.md)
- [Testing cache](../codebase/TESTING.md)

## Related

- [Operations index](index.md)