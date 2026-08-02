# Loop Registry

**Cache is king.** Every loop loads manifest + cache before any source scan, `gh` deep-dive, or sub-agent spawn. Read `VISION.md` each run. After verifier PASS, run `/loop-compound` (steps 10–14). See `loop-budget.md` and `/cache-efficient`.

Promotion pipeline: `feature/*` → `develop` → `master` (production).

## Active loops

| Loop | Cadence | Level | Maker | Verifier | Cache files (required) |
|------|---------|-------|-------|----------|----------------------|
| [daily-triage](patterns/daily-triage.md) | Weekdays 09:00 UTC | **L1** report-only | `loop-triage` | `loop-verifier` | `README.md`, `CONCERNS.md`, `TODO`, `STATE.md` |
| [cache-freshness-watch](patterns/cache-freshness-watch.md) | Mondays 09:30 UTC | L1 | `cache-freshness-check` | `loop-verifier` | `.codebase-scan.txt`, `README.md`, `TODO`, `STATE.md` |
| [chain-health-watch](patterns/chain-health-watch.md) | Mondays 09:30 UTC | L1 | `loop-engineering` | `loop-verifier` | `chains/registry.yaml`, `CHAIN.md`, `STATE.md` |
| [github-ci-watch](patterns/github-ci-watch.md) | Mondays 09:30 UTC | L1 | `github-workflow-expert` | `loop-verifier` | `INTEGRATIONS.md`, workflow list, `STATE.md` |
| [repo-health-watch](patterns/repo-health-watch.md) | Mondays 09:30 UTC | L1 | `github-expert` + `git-workflow-guardrails` | `loop-verifier` | `CONVENTIONS.md`, `INTEGRATIONS.md`, `STATE.md` |
| [security-flywheel-watch](patterns/security-flywheel-watch.md) | Mondays 09:30 UTC (manual OK) | L1 | `loop-security-flywheel-host.sh` + optional `/chain security-flywheel` | `loop-verifier` | `SECURITY.md`, flywheel guide, peers |
| branch-promotion-watch | On push `feature/**`, `develop` | L1 | `github-expert` | human | `CONVENTIONS.md`, `STATE.md` |

## Scaffolded (manual — not scheduled)

See [When to use loops](docs/guides/when-to-use-loops.md). Enable cron only after `bash scripts/loop-audit.sh` ≥ 80 + human approval.

| Loop | Cadence | Level | Maker | Verifier | Cache files (required) |
|------|---------|-------|-------|----------|----------------------|
| [vault-integrity-watch](patterns/vault-integrity-watch.md) | **Manual** `/chain vault-integrity-watch` | L1 | `loop-engineering` | `loop-verifier` | `STATE.md`, `VISION.md`, `LOOP.md` |
| [version-drift-watch](patterns/version-drift-watch.md) | **Manual** `/chain version-drift-watch` | L1 | `loop-engineering` | `loop-verifier` | `VERSION`, `STATE.md`, `LOOP.md`, `TODO/` |
| [wiki-lint-watch](patterns/wiki-lint-watch.md) | **Manual** `/chain wiki-lint-watch` | L1 | `llm-wiki` lint | `loop-verifier` | `wiki/index.md`, `wiki/log.md`, `STATE.md`, `LOOP.md` |

Host snapshots: `scripts/loop-vault-integrity-host.sh`, `scripts/loop-version-drift-host.sh`, `scripts/loop-wiki-lint-host.sh`.

## Levels

| Level | Behaviour | Auto-fix |
|-------|-----------|----------|
| **L1** | Cache synthesis → report in `reports/loops/` + `STATE.md` | No |
| **L2** | Assisted fixes in worktree; PR draft | Only allowlisted paths |
| **L3** | Unattended merge gates | Not enabled in this template |

## Invocation

| Tool | Command |
|------|---------|
| Grok | `/loop 1d Run loop-triage per patterns/daily-triage.md. Cache-first. L1 only.` |
| Claude Code | `/loop-triage` then `/loop-verifier` on the report artifact |
| GitHub Actions | `.github/workflows/loop-daily-triage.yml` (weekday host); `.github/workflows/loop-weekly-watch.yml` (Monday host) |
| Grok (weekly) | `/chain cache-freshness-watch`, `/chain chain-health-watch`, `/chain github-ci-watch`, `/chain repo-health-watch` |
| GitHub Actions (chain) | `.github/workflows/run-chain.yml` — `workflow_dispatch` with `chain_id` |

## On-demand patterns (not scheduled)

| Pattern | Doc | Entry |
|---------|-----|-------|
| compound-learning | [patterns/compound-learning.md](patterns/compound-learning.md) | `/loop-compound` after every verifier PASS |
| perspective-guided-discovery | [patterns/perspective-guided-discovery.md](patterns/perspective-guided-discovery.md) | `/acquire-codebase-knowledge`, `/documentation-specialist`, `/chain research-deep-dive`, `/orchestrator` with `discovery_mode: true` |

Registered in `patterns/registry.yaml` under `patterns:` (distinct from scheduled `loops:`). L1 daily triage does **not** auto-run these.

## Adding a loop

1. Add pattern under `patterns/` and entry in `patterns/registry.yaml`.
2. Register here with required cache files and token tier.
3. Run `bash scripts/loop-audit.sh` — target score ≥ 80 before enabling schedule.