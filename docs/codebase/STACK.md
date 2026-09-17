# Stack

[UPDATED 2026-09-17] — product **3.0.0** lockstep (CLI + npm + extension). Prior cache 2026-08-16.

> Lens: Operator, Developer — evidence from manifest, `pyproject.toml`, `package.json`, `extensions/vscode-orchestrator/package.json`, scan `=== DETECTED STACK ===`.

## Repository Type

**Dual-nature repo:** (1) portable **orchestrator template** (skills, chains, loops, cache) and (2) shipped **Orchestrator Memory** product — Python host CLI + npm wrapper + VS Code/Cursor extension. Not an application web stack (no Laravel/`app/`). Manifest `stack.framework: generic` is **correct** for this source repo.

## Manifest vs scan

| Source | Framework | Language | Database | Runtime |
|--------|-----------|----------|----------|---------|
| `.grok/project-manifest.yaml` (and synced copies) | generic | generic | none / `uses_database: false` | `local` |
| `scan.py` file signals | — | Node (`package.json`) + Python (`pyproject.toml`) | — | chains + LOOP present |

No `[ASK USER]` on stack engine: generic + local is intentional. SQLite at `reports/memory/memory.db` is a **local token-cache file**, not a declared application database.

## Product versions (lockstep)

| Artifact | Version | Evidence |
|----------|---------|----------|
| Template / CLI | **3.0.0** | `/VERSION`, hatch `tool.hatch.version` |
| npm `@ndestates/orchestrator` | 3.0.0 | root `package.json` (publish only after matching Release wheel) |
| VSIX `ndestates.orchestrator-memory` | 3.0.0 | `extensions/vscode-orchestrator/package.json` |
| MCP package | 0.1.0 | `mcp-server/pyproject.toml` |

## Languages and runtimes

| Layer | Runtime | Notes |
|-------|---------|--------|
| Host CLI | Python ≥3.10 | Package `orchestrator`; entry `orchestrator_cli.__main__:main`; hatchling; `uv.lock` present |
| npm wrapper | Node ≥18 | `bin/orchestrator.js`; `postinstall` → `scripts/npm/postinstall.js` |
| VS Code / Cursor extension | VS Code ^1.90 | `extensions/vscode-orchestrator/extension.js`; publisher `ndestates` |
| MCP server | Python ≥3.10 | `orchestrator-mcp`; `mcp[cli]>=1.28.0,<2` (pin: mcp 2.0 renamed FastMCP) |
| Tests | pytest ≥7 | Root `tests/` + `mcp-server/tests/` |
| Agent scripts | Python 3 + Bash | `scripts/*.py` (61), `scripts/*.sh` (41) |

No Docker / Compose / DDEV in **this** repo (`scan.py` `=== DOCKER ===` empty). DDEV snippets exist only for **app-repo** MCP (`mcp-server/ddev/`).

## Tooling

| Tool | Use |
|------|-----|
| Python 3.12 in CI | `.github/workflows/tooling-tests.yml` |
| pytest | `PYTHONPATH=scripts pytest tests -q` |
| GitHub CLI (`gh`) | PRs, workflow dispatch |
| GitHub Actions | 13 workflows; Node 24 pin (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`) |
| ripgrep | host tool check via `scripts/install-host-tools.sh` |
| Optional Ollama | `scripts/install-ollama.sh`; model-route catalog |

## AI surfaces (this install)

| Surface | Root | Role |
|---------|------|------|
| Grok Build | `.grok/` | **Source of truth** for skills/prompts/agents |
| GitHub Copilot | `.github/` + `.copilot/` | Synced + workflows + canonical manifest |
| Claude Code | `.claude/` | Commands + agents |
| Cursor | `.cursor/` | Commands + rules |
| Gemini | `.gemini/` | Instructions + prompts |
| ChatGPT | `.chatgpt/` | Instructions + prompts |
| MCP clients | `mcp-server/` | Dev-only tools |

## Token policy (lean)

- `max_cache_files_default: 2` extra `docs/codebase/*` after spine
- `cache_stale_days: 14`
- `grep_before_read: true`, `no_source_until_confirmed: true`
- Chain handoffs ≤80 tokens
- L1 loops: 0 application source reads

## Inventory (2026-08-16)

| Surface | Count |
|---------|-------|
| `.grok/skills/*/SKILL.md` | 83 |
| `.grok/prompts/*.md` | 19 |
| `.grok/agents/*.md` | 32 |
| `.claude/commands/*.md` | 97 |
| `.claude/agents/*.md` | 35 |
| `.github/skills/` | 82 |
| `.github/agents/` | 35 |
| `.github/workflows/*.yml` | 13 |
| `.copilot/skills/` | 82 |
| `tests/test_*.py` | 59 |
| `mcp-server/tests/test_*.py` | 4 |
| `chains/registry.yaml` `- id:` | 155 |

## Evidence

- `.grok/project-manifest.yaml`, `.github/project-manifest.yaml`
- `docs/codebase/.codebase-scan.txt` (`=== DETECTED STACK ===`, generated 2026-08-16)
- `VERSION`, `pyproject.toml`, `package.json`, `uv.lock`
- `extensions/vscode-orchestrator/package.json`
- `mcp-server/pyproject.toml`
- `ls` counts over `.grok/`, `.claude/`, `.github/`, `tests/`
