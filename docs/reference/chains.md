# Chains reference

[UPDATED 2026-07-07]

## Overview

Chains are defined in `chains/registry.yaml` and summarized in `CHAIN.md`. Invoke with `/chain <id>` or matching intent.

## Before you begin

- [Chains and skills guide](../guides/chains-and-skills.md) for usage patterns

## Active chains

| Id | Steps | Tier | Use when |
|----|-------|------|----------|
| `session-start` | load-cache → standup → cache-efficient | low | Default session |
| `loop-daily` | loop-triage → loop-verifier | low | L1 triage |
| `cache-freshness-watch` | cache-freshness-check → loop-verifier | low | Weekly cache staleness (Mon) |
| `chain-health-watch` | loop-engineering → loop-verifier | low | Weekly chain registry audit (Mon) |
| `github-ci-watch` | github-workflow-expert → loop-verifier | low | Weekly Actions health (Mon) |
| `repo-health-watch` | github-expert → git-workflow → loop-verifier | low | Weekly branch/PR hygiene (Mon) |
| `documentation-full` | load-cache → read-codebase → readme → documentation-specialist | high | Full doc site |
| `documentation-refresh` | load-cache → readme → documentation-specialist | medium | Doc update |
| `delivery` | branch → git → test-safety → tests | medium | Commit/push/PR |
| `promote-master` | branch → git gates → github PR sync → git promote | medium | Merge develop into master |
| `migration-safe` | schema check → audit → test-safety → mysql/mariadb/sqlite | medium | Migrations |
| `database-design` | data-architect → model-check → Laravel → engine → Filament | medium | ER + Eloquent alignment |
| `laravel-database-design` | data-architect → model-check → Laravel → engine → Filament | high | Full Laravel/Filament DB design |
| `vector-db-assess` | load-cache → vector fit assessment | low | Should project use vectors? |
| `vector-db-setup` | assess → architect → vector-db → Laravel → engine | medium | Vector / RAG after fit pass |
| `security-review` | security-audit → test-safety | medium | Auth review |
| `cyber-essentials-review` | cyber-security-essentials → security-audit | medium | UK NCSC Cyber Essentials |
| `cyber-essentials-hunt` | load-cache → CE → bug-hunt → security | high | CE + defect hunt |
| `cyber-essentials-pre-deploy` | drift → CE → pre-deploy hunt → security | high | CE before release |
| `cyber-essentials-maturity` | CE → ai-maturity → security | medium | CE + SDLC maturity |
| `deploy-check` | drift → docker → workflows → git → DO → eval | high | Production deploy |
| `docker-deploy` | docker → workflows → github → git → DO | high | Hardened container CI |
| `deploy-dns-infra` | Route53 → DO firewall → SES → git | high | Prod DNS + DKIM + perimeter |
| `repo-health` | github → git → drift | medium | Repo hygiene |
| `eod-shutdown` | todo → readme → ddev-cleanup | low | End of day |
| `template-deploy` | load-cache → orchestrator-deploy | medium | Deploy .grok + chains to target |
| `complex-task` | load-cache → orchestrator | high | Multi-domain work |
| `loop-engineering-audit` | load-cache → loop-engineering | low | Loop maturity |
| `pre-flight` | branch → drift → test-safety | medium | Before starting work |
| `laravel-feature` | load-cache → branch → laravel → tests | medium | Laravel/Filament |
| `filament-review` | load-cache → filament-review → security | medium | Panel audit |
| `paypal-setup` | drift → paypal-billing | medium | PayPal integration |
| `prod-db-ops` | drift → prod-db → eval | high | Prod DB maintenance |
| `cache-rebuild` | load-cache → read-codebase | high | Full cache refresh |
| `ai-maturity` | load-cache → ai-engineering-maturity | low | Maturity assessment |
| `web-design` | load-cache → web-build-design → readme | medium | Marketing pages |
| `beta-ready` | load-cache → beta-checklist → drift | medium | Pre-beta readiness |
| `bug-hunt` | load-cache → bug-hunter (scan) | medium | Report only |
| `bug-hunt-fix` | hunt (fix) → test-safety → tests | high | Safe fixes + verify |
| `bug-hunt-deep` | deep hunt → security → schema → tests | high | Full report pass |
| `bug-hunt-fix-deep` | deep fix → security → tests → schema | high | Fix + security + tests |
| `bug-hunt-pre-deploy` | drift → hunt → security → test-safety | high | Pre-release report |
| `bug-hunt-pre-deploy-fix` | drift → hunt fix → security → tests | high | Pre-release with fixes |

Fix chains honour `fix_policy`: low/medium auto-fix; critical/high suggest unless approved; **rollback mandatory** via `bug-hunt-backup.py` except **critical security** fixes (kept on rollback).

Optional steps (e.g. `read-codebase` in `documentation-full`) run when cache is stale or user requests full refresh.

### Scheduled allowlist

Chains in `chain_policy.scheduled_allowlist` skip the confirm prompt when invoked with explicit id + `scheduled` (or `CHAIN_SCHEDULED=1`). See [Manifest](manifest.md).

### Chain completion

After any successful `/chain` run, use `bash scripts/chain-completion-write.sh` to append `loop-run-log.md` and refresh `STATE.md` → `## Last chain run`.

**Single registry:** `chains/registry.yaml` holds both `skills:` (inventory) and `chains:` (composition). Skill content remains in `.grok/skills/`.

## Audit

```bash
bash scripts/chain-audit.sh
```

## Verify

Score 100/100; all `invoke` targets resolve under `.grok/skills/` or `.grok/prompts/`.

## Next steps

- [Skills](skills.md)
- [Testing](../operations/testing.md)
- [Manifest](manifest.md)

## Related

- [Reference index](index.md)
- [CHAIN.md](../../CHAIN.md) — human registry