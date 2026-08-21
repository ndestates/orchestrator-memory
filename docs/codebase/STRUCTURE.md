# Structure

[UPDATED 2026-08-16] — added CLI (`src/`), VSIX (`extensions/`), `tests/`, `wiki/`, extra AI surfaces. See getting-started/project-overview.md.

> Lens: Developer — evidence from `scan.py` `=== TREE ===` and repo listing 2026-08-16.

## Top-Level Layout

```
.
├── .grok/                  # Grok skills/prompts/agents/memories (SOURCE OF TRUTH)
├── .github/                # Copilot + workflows + canonical manifest
├── .claude/                # Claude Code commands + agents
├── .copilot/               # Copilot memories + mirrored skills
├── .cursor/                # Cursor commands + rules
├── .gemini/                # Gemini instructions + prompts
├── .chatgpt/               # ChatGPT instructions + prompts
├── src/orchestrator_cli/   # Installable host CLI (Python)
├── bin/orchestrator.js     # npm bin wrapper
├── extensions/vscode-orchestrator/  # VS Code/Cursor extension (VSIX)
├── mcp-server/             # Python MCP server (orchestrator-mcp)
├── chains/                 # registry.yaml + slash-catalog
├── patterns/               # Loop + watch patterns
├── starters/               # Loop starter templates
├── schemas/                # skill.schema.json
├── scripts/                # sync, audits, session, deploy, security
├── tests/                  # pytest harness for tooling/CLI
├── services/license-api/   # Optional private entitlement (not required)
├── wiki/ + raw/            # LLM wiki (lean) + raw ingest
├── docs/                   # Human docs + docs/codebase cache
├── TODO/                   # Daily YYYY-MM-DD_TODO.md
├── reports/                # loops, vault, sessions, memory, security, tokens
├── LOOP.md, STATE.md, VISION.md
├── CHAIN.md
├── VERSION, package.json, pyproject.toml
└── SECURITY.md
```

Generated / local-only (do not treat as architecture): `dist/`, `reports/memory/memory.db`, `__pycache__/`, most of `reports/sessions/`.

## `.grok/` (primary)

| Path | Count / notes |
|------|----------------|
| `skills/*/SKILL.md` | 83 (incl. session-start, chain, memory, wiki, skills.sh complements) |
| `prompts/*.md` | 19 |
| `agents/*.md` | 32 |
| `memories/INDEX.md` | Tier-1/2 routing |
| `project-manifest.yaml` | Grok copy (canonical edit: `.github/`) |

## Other AI surfaces

| Path | Purpose |
|------|---------|
| `.github/project-manifest.yaml` | Canonical manifest; `sync_manifests.py` copies out |
| `.github/workflows/` | 13 Actions workflows |
| `.claude/commands/` (97) + `agents/` (35) | Claude slash + subagents |
| `.copilot/skills/` (82) | Copilot mirror |
| `.cursor/commands/` (83 files) + `rules/` | Cursor surface |
| `.gemini/`, `.chatgpt/` | Instructions + prompts + MCP examples |

## Product code

| Path | Purpose |
|------|---------|
| `src/orchestrator_cli/` | `init`/`upgrade`/`memory`/`license`/`version`; hatch stages a residue-filtered template |
| `bin/orchestrator.js` + `scripts/npm/` | npm install path |
| `extensions/vscode-orchestrator/` | Chat participant `@orchestrator`; slash `/session-start`, `/chain`, `/memory-brief` |
| `mcp-server/src/orchestrator_mcp/` | Cache-first MCP tools; stdio + HTTP |
| `services/license-api/` | Optional DO App Platform packaging of license server |

## `scripts/`

| Group | Examples |
|-------|----------|
| Session | `session-spinup-bundle.py`, `session-context-envelope.py`, `session-resume-brief.py`, `session-security-sweep.sh` |
| Sync | `sync_grok_to_github_claude.py`, `sync_manifests.py` |
| Deploy | `deploy_grok_to_project.py`, `orchestrator-app-update.sh`, `deploy-bundle.yaml` |
| Audits | `chain-audit.sh`, `loop-audit.sh`, `check_name_alignment.py`, `orchestrator-malware-lint.py` |
| Memory / wiki | `memory_agent.py`, `session-memory-brief.py`, `session-wiki-brief.py` |
| Cache | `generate-cache-sections.py`, acquire-codebase `scan.py` |

**Wave fleet scripts are gone** (`tests/test_wave_absent.py`). Install path is per-app `orchestrator init` / `upgrade`.

## `tests/`

59 `test_*.py` files covering CLI, deploy, session envelope, vault/guardrails, wave-absent, workstreams, malware lint. MCP tests live separately under `mcp-server/tests/` (4 files).

## Evidence

- `docs/codebase/.codebase-scan.txt` (`=== TREE ===`, generated 2026-08-16)
- `src/orchestrator_cli/`, `extensions/vscode-orchestrator/package.json`
- `tests/`, `mcp-server/`, `wiki/index.md`
- `scripts/generate-cache-sections.py`
