# Architecture

[UPDATED 2026-07-07] — full docs site update alignment (vault graph, secure self-building ledger, multi-AI, manifest vault paths). See human docs: project-overview.md, guides/knowledge-vault.md, reference/manifest.md.

## System Purpose

Manifest-first, cache-first **orchestration template** — coordinates AI agents via prompts and skills, not application runtime code. Distributes the same surface to four AI tools (Grok, Copilot, Claude Code, MCP clients) from one source.

## Core Model

```
.github/project-manifest.yaml  (≡ .claude/ copy)
   stack, paths, token_policy, loop_policy, chain_policy, agent_policy
        ↓
docs/codebase/* + TODO/ + STATE.md + memories INDEX   (the cache)
        ↓
Entry: load-cache | /chain | /orchestrator | loop-triage | MCP tools
        ↓
Specialist agents/skills (security, tests, github, laravel, python, frontend, …)
```

## Composition Layers

| Layer | Registry | Maker | Checker |
|-------|----------|-------|---------|
| **Chains** (on-demand) | `CHAIN.md`, `chains/registry.yaml` | `/chain` | user opt-out menu; `loop-verifier` on watch chains |
| **Loops** (scheduled) | `LOOP.md`, `patterns/registry.yaml` | `loop-triage`, weekly watches | `loop-verifier` |
| **Orchestrator** (ad-hoc) | `orchestrator` prompt/agent | orchestrator | human approval gates |
| **MCP** (tool API) | `mcp-server/` | client agent | path sandbox + audit log |

## Loop Architecture

- **L1 only** in this template (report-only; no auto-fix, no source reads). L2/L3 defined but disabled (`loop_policy.allow_l2: false`).
- **Daily:** `daily-triage` (weekdays 09:00 UTC) → `reports/loops/*.md` + `STATE.md`.
- **Weekly (Mon 09:30 UTC):** `cache-freshness-watch`, `chain-health-watch`, `github-ci-watch`, `repo-health-watch`.
- **Event:** `branch-promotion-watch` on push to `feature/**`/`develop`.
- **On-demand:** `perspective-guided-discovery` — multi-lens questioning before source reads.
- Durable spine + **secure self-building vault**: `STATE.md` + `loop-run-log.md` + `loop-budget.md` + hash-chained graph ledger (`reports/vault/events.jsonl` via `scripts/_engine/vault.py` + `vault_synthesis.py`). Graph provides provenance, tamper-evidence (content hashes + parents), secret scrubbing at emission, verify on compound, and lean subgraph loading. Integrated into loop-compound and chain completion. See human guide: guides/knowledge-vault.md; overview: getting-started/project-overview.md.

### Half-loop pattern (host + agent)

GitHub Actions jobs write **host snapshots** only (`scripts/loop-*-host.sh`). The agent completes the chain (`/chain <watch> scheduled`) and verifier. `scripts/chain-completion-write.sh` closes the loop into `STATE.md` and `loop-run-log.md`.

### Trusted scheduled chains

`chain_policy.scheduled_allowlist` permits skip-confirm runs for `session-start`, weekly watch chains, and `eod-shutdown` when invoked with explicit id + `scheduled`.

## Sync Architecture

- **Source of truth:** `.grok/skills/*/SKILL.md`, `.grok/prompts/*.md`, `.grok/agents/*.md`
- **Targets:** `.github/skills|prompts|agents/`, `.claude/commands|agents/`, `.copilot/skills/`, `.github/copilot-instructions.md`
- **Driver:** `scripts/sync_grok_to_github_claude.py` — adapts slash-command paths and renames per target (e.g. `todo-specialist-agent` → `todo-specialist`).
- **Manifest copies:** `python3 scripts/sync_manifests.py` — `.github/project-manifest.yaml` → per-platform manifests.

## Deploy Architecture (template → app repos)

- `scripts/deploy_grok_to_project.py` copies selectable bundles (`.grok`, `.github`, `.claude`, `.copilot`, `mcp`) to a target repo, tracking customized files in `deploy-state.json` with overwrite/skip/merge handling.
- `scripts/stack-profiles/*.yaml` + `manifest-map.yaml` apply per-stack manifest/skill overrides (laravel, python-flask, google/facebook-stats).
- **Per-app only:** fleet wave tooling is permanently removed; use `orchestrator init|upgrade` (or `deploy_grok_to_project.py`) on one app at a time.

## MCP Architecture

- `orchestrator_mcp.server` exposes cache-first **tools** (`health_check`, `get_project_manifest`, `get_cache_freshness`, `read_cache_file`, `get_latest_todo`, `get_loop_state`, `list_chains`, `get_chain_detail`, `list_skills`, `get_skill_summary`, `run_readonly_audit`) and **resources** (manifest, cache index, chains registry, latest TODO, loop state, session-start hint).
- Read-only by design: `run_readonly_audit` is allowlisted to `chain-audit.sh`, `loop-audit.sh`, `check_name_alignment.py`. All reads sandboxed to `PROJECT_ROOT` (`sandbox.py`); every call appended to JSONL audit (`audit.py`, `reports/mcp/`).

## Branch Promotion

- Workflow: `.github/workflows/branch-promotion-prs.yml`
- Push `feature/**` → draft PR to `develop`; push `develop` → draft PR to `master`.
- Requires repo setting: Actions may create/approve PRs.

## Key Files

- `.grok/prompts/orchestrator*.md` — single/multi-lane planning (Shape A/B)
- `.github/copilot-instructions.md` — security and session rules (synced)
- `scripts/chain-audit.sh`, `scripts/loop-audit.sh` — registry validation gates
- `scripts/chain-completion-write.sh`, `scripts/run-chain-host.sh` — chain run audit + dispatch prep

## Evidence

- `LOOP.md`, `loop-budget.md`, `STATE.md`
- `mcp-server/README.md`, `mcp-server/src/orchestrator_mcp/server.py` (tool/resource definitions)
- `scripts/deploy_grok_to_project.py`, `scripts/sync_grok_to_github_claude.py`, `scripts/deploy-bundle.yaml`
- `patterns/chain-health-watch.md`, `patterns/repo-health-watch.md`
- Lens: Developer, Operator (sync/deploy/loops), Security (MCP sandbox)