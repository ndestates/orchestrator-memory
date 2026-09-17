# Architecture

[UPDATED 2026-08-16] — product surfaces (CLI, VSIX, memory, wiki) + session envelope. Human: project-overview.md, guides/knowledge-vault.md, guides/always-on-memory.md.

> Lens: Product, Developer, Operator — evidence from README, `src/orchestrator_cli/`, `extensions/`, `mcp-server/`, LOOP/CHAIN, session scripts.

## System Purpose

Two coupled products in one tree:

1. **Orchestrator template** — manifest-first, cache-first agent orchestration (skills, chains, loops) deployed into app repos.
2. **Orchestrator Memory** — local SQLite token cache + vault dual-write so any assistant starts from a lean brief. Shipped as VS Code/Cursor extension + `orchestrator` CLI.

## Core Model

```
VERSION (2.2.5)
   ↓
.github/project-manifest.yaml  →  sync_manifests.py  →  .grok/.claude/.cursor/.gemini/.chatgpt
   stack, paths, token_policy, loop_policy, chain_policy, wiki_policy, memory_policy
        ↓
docs/codebase/* + TODO/ + STATE.md + resume card + memories INDEX
        ↓
Session: session-spinup-bundle.py  (fetch → remote_last → card → situation)
        ↓
Entry: /chain session-start | /chain session-resume | /load-cache | MCP tools | @orchestrator
        ↓
Specialist skills/agents  +  memory.db (runtime)  +  vault events.jsonl (durable)
```

## Composition Layers

| Layer | Registry | Maker | Checker |
|-------|----------|-------|---------|
| **Chains** (on-demand) | `CHAIN.md`, `chains/registry.yaml` | `/chain` | opt-out; `loop-verifier` on watches |
| **Loops** (scheduled) | `LOOP.md`, `patterns/registry.yaml` | `loop-triage`, weekly watches | `loop-verifier` |
| **Orchestrator** (ad-hoc) | orchestrator prompt/agent | orchestrator | human approval gates |
| **Memory** | `reports/memory/memory.db` | `memory_agent.py` / extension | vault dual-write + scrubbing |
| **Wiki** (lean) | `wiki/index.md` | `/llm-wiki` ingest/query/lint | L1 approval for writes |
| **MCP** | `mcp-server/` | client agent | sandbox + audit JSONL |

## Session architecture

| Command | When | Land on |
|---------|------|---------|
| `/chain session-start` | New day or after `/chain eod-shutdown` | `remote_last` (team tip), then card |
| `/chain session-resume` | Same calendar day after `/chain session-end` | **Prior session Branch** from GitHub after fetch (origin session-end card), or this machine if the pause was never pushed. Not `remote_last`. Fast-forward if behind and clean. |

When `resume_first=yes` (fresh card, branch match): card is authoritative; skip full TODO/STATE/VISION. Start: `session-spinup-bundle.py` / envelope `--write`. Resume: `session-resume-land.py` then envelope `--resume-session`.

## Loop architecture

- **L1 only** (`loop_policy.allow_l2: false`) — report-only, no auto-fix, no source reads.
- **Daily:** `daily-triage` weekdays 09:00 UTC.
- **Weekly Mon 09:30 UTC:** cache-freshness, chain-health, github-ci, repo-health, security-flywheel (manual OK).
- **Event:** `branch-promotion-watch` on `feature/**` / `develop`.
- **Manual scaffolded:** vault-integrity, version-drift, wiki-lint.
- Durable spine: `STATE.md` + `loop-run-log.md` + `loop-budget.md` + hash-chained vault (`reports/vault/events.jsonl`).

### Half-loop (host + agent)

Actions write host snapshots (`scripts/loop-*-host.sh`). Agent completes `/chain <watch> scheduled`. `chain-completion-write.sh` closes into STATE + run log.

## Sync architecture

- **Source:** `.grok/skills|prompts|agents`
- **Targets:** `.github/`, `.claude/`, `.copilot/` (plus Cursor/Gemini/ChatGPT manifests via `sync_manifests.py`)
- **Driver:** `scripts/sync_grok_to_github_claude.py`
- Surface counts **diverge by design** (prompts also become Claude commands).

## Deploy architecture (template → one app)

- Preferred: `orchestrator init` / `upgrade` or `scripts/orchestrator-app-update.sh`
- Low-level: `scripts/deploy_grok_to_project.py` + `deploy-bundle.yaml` selections
- Stack overlays: `scripts/stack-profiles/`
- **Fleet wave tooling deleted** (guard: `tests/test_wave_absent.py`)

Wheel build stages a residue-filtered template into `orchestrator_cli/template/` (`hatch_build.py` + `scripts/_engine/public_pack.py`). Factory-only app files are omitted.

## Product packaging

| Artifact | Builder | Publish |
|----------|---------|---------|
| Python wheel + sdist | hatchling / `product-release.yml` | GitHub Release |
| VSIX | `vscode-marketplace.yml` | Artifact + **human** Marketplace upload (optional `VSCE_PAT`) |
| npm `@ndestates/orchestrator` | `package.json` | npmjs (after matching GitHub Release wheel) |

## MCP architecture

`orchestrator_mcp.server`: cache-first tools (`get_project_manifest`, `read_cache_file`, `get_latest_todo`, `get_chain_detail`, …) and resources. `run_readonly_audit` allowlisted. Reads sandboxed to `PROJECT_ROOT`. HTTP fail-closed without `ORCHESTRATOR_MCP_API_KEY` (loopback keyless only with `--allow-insecure-http`). Policy: `mcp: off` default; `dev_only` never on public hosts.

## Branch promotion

`.github/workflows/branch-promotion-prs.yml`: push `feature/**` → draft PR to `develop`; push `develop` → draft PR to `master`. Needs “Actions may create PRs”.

## Key files

- `scripts/session-spinup-bundle.py` — one-shot session CTX
- `scripts/memory_agent.py` — always-on memory
- `extensions/vscode-orchestrator/extension.js` — IDE surface
- `src/orchestrator_cli/__main__.py` — CLI
- `SECURITY.md` — trust map

## Evidence

- `README.md`, `VERSION`, `LOOP.md`, `CHAIN.md`
- `pyproject.toml` (hatch force-include), `package.json`
- `mcp-server/src/orchestrator_mcp/`, `mcp-server/pyproject.toml`
- `scripts/deploy_grok_to_project.py`, `tests/test_wave_absent.py`
- Lens: Developer, Operator, Security (MCP/sandbox), Product
