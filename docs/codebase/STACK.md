# Stack

[UPDATED 2026-07-07]

## Repository Type

**Orchestrator template** — documentation, prompts, agents, and automation config. No application runtime (no Laravel/Node app in this repo). The one piece of shippable code is the **MCP server** (`mcp-server/`, Python package `orchestrator-mcp`), a dev-only agent tool — not a production service.

## Manifest Defaults

| Field | Value |
|-------|-------|
| `framework` | generic |
| `language` | generic |
| `uses_database` | false |

Vault paths (self-building knowledge): `vault_events_dir`, `vault_ledger` (see reference/manifest.md and guides/knowledge-vault.md for human docs).
| `environment_manager` | local |
| `default_branch` | master |

Manifest exists in two mirrored copies: `.github/project-manifest.yaml` and `.claude/project-manifest.yaml` (kept in sync; both are loaded by their respective tools).

## Tooling

| Tool | Use |
|------|-----|
| Python 3 (≥3.10 for MCP) | `scripts/sync_grok_to_github_claude.py`, `deploy_grok_to_project.py`, `mcp-server/` |
| Bash | `chain-audit.sh`, `loop-audit.sh`, wave-deploy scripts, workflow host helpers |
| GitHub CLI (`gh`) | PR promotion, triage snapshots, workflow dispatch |
| GitHub Actions | Release, repo sync, loop triage (daily + weekly), branch promotion, chain audit |
| YAML | Manifests, chain/loop/pattern registries, stack-profiles, workflows |

## MCP Server (`mcp-server/`)

- Package: `orchestrator-mcp` v0.1.0 (`pyproject.toml`, hatchling build).
- Dependencies: `mcp[cli]>=1.2.0`, `pyyaml>=6.0`. Python `>=3.10`.
- Transports: `stdio` (local, no auth) and `streamable-http` (API-key auth).
- Entry point: `orchestrator-mcp = orchestrator_mcp.server:main`.

## AI Surfaces

| Surface | Invoke style | Source |
|---------|--------------|--------|
| Grok Build/CLI | `/skill-name`, `/chain`, `/load-project-cache-first` | `.grok/skills/*/SKILL.md` (source of truth) |
| GitHub Copilot | slash skills | `.github/skills/*/SKILL.md` (synced) |
| Claude Code | `/command-name` | `.claude/commands/*.md` (synced) |
| MCP clients (Cursor/Grok) | tool calls | `mcp-server/` |

## Inventory (counts)

| Surface | Count |
|---------|-------|
| `.grok/skills/` | 46 |
| `.grok/prompts/` | 10 |
| `.grok/agents/` | 16 |
| `.claude/commands/` | 48 |
| `.claude/agents/` | 19 |
| `.github/skills/` | 45 |
| `scripts/*.sh|*.py` | 34 |
| `.github/workflows/` | 7 |
| chains/registry.yaml entries (skills + chains) | 84 |

## Token Policy (lean)

- `max_cache_files_default: 2` (additional `docs/codebase/*` after spine)
- `cache_stale_days: 14`
- Chain handoff cap: 80 tokens (`chain_policy.max_handoff_tokens`)
- L1 loops: 0 source file reads
- `grep_before_read: true`, `no_source_until_confirmed: true`

## Evidence

- `.claude/project-manifest.yaml`, `.github/project-manifest.yaml`
- `docs/codebase/.codebase-scan.txt` (`=== DETECTED STACK ===`, generated 2026-06-23)
- `mcp-server/pyproject.toml`, `mcp-server/README.md`
- Counts from `ls` over `.grok/`, `.claude/`, `.github/`, `scripts/`, `chains/registry.yaml`
