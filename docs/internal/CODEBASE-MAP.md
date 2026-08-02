# Codebase map (internal)

> **INTERNAL — not for public release.** Structural map of the orchestrator **template** repo (not a single SaaS app).

## 1. What this repository is

A **manifest-first, cache-first AI delivery template**: skills, agents, chains, loops, MCP server, CLI installer, and deploy tooling used to accelerate forked app repos (Laravel, etc.) and to operate the orchestrator itself.

- **Not** primarily application domain code (Filament panels live in *app* repos).  
- **Is** the control plane for agents, security gates, session workflow, and upgrades.

**Version source of truth:** `/VERSION` (synced to `package.json`, `scripts/orchestrator-template-version`).

## 2. Top-level layout

| Path | Role |
|------|------|
| `.grok/` | Grok Build skills, agents, config, memories, references |
| `.claude/` | Claude Code commands, agents, manifest |
| `.github/` | Canonical-ish GitHub surfaces: workflows, skills, prompts, agents, copilot-instructions, canonical `project-manifest.yaml` |
| `.copilot/` | Copilot workspace mirror of skills/manifest |
| `.gemini/` | Gemini prompts + instructions |
| `.cursor/` | Cursor rules + mcp.json + manifest |
| `scripts/` | Host tooling (Python/bash) — session, deploy, security, loops |
| `scripts/_engine/` | Importable libraries (vault, deploy, untrusted_text, envelope, …) |
| `mcp-server/` | Orchestrator MCP package (stdio/HTTP) |
| `src/orchestrator_cli/` | Python CLI (`orchestrator` entry via npm wrapper) |
| `chains/` | Chain registry (`registry.yaml`, templates) |
| `docs/` | Public-ish docs site material |
| `docs/internal/` | **This internal-only tree** |
| `docs/codebase/` | Agent cache spine (ARCHITECTURE, STACK, …) |
| `TODO/` | Daily operator TODOs (untrusted DATA) |
| `reports/` | Security sweeps, vault, tokens, research, sessions |
| `wiki/` + `raw/` | LLM Wiki (Karpathy pattern), lean mode |
| `tests/` | Tooling pytest suite |
| `patterns/` | Loop patterns |
| `starters/` | Templates for loop state etc. |
| `vscode-extension/` | VS Code marketplace wrapper (optional) |

## 3. Core runtime concepts

### 3.1 Manifest

- **Canonical edit:** often `.github/project-manifest.yaml` then `python3 scripts/sync_manifests.py`  
- **Per host copy:** `.grok/`, `.claude/`, `.copilot/`, `.gemini/`, `.cursor/`  
- **Controls:** stack, paths, `token_policy`, `chain_policy`, `loop_policy`, `security_policy`, `wiki_policy`, agent_policy  

### 3.2 Cache-first

Agents load `docs/codebase/*` + TODO + STATE before source.  
Caps: `token_policy.max_cache_files_default` (lean default 2 extra files).

### 3.3 Session-start

Preferred path:

```bash
python3 scripts/session-context-envelope.py --write
```

Produces fixed-size CTX: identity, MCP dev-only, pickup, platform surface, version, open/next.  
Then optional security sweep, vault brief, lean cache.

### 3.4 Chains

Declared in `chains/registry.yaml`. Run via `/chain <id>` or intent.  
Skill: `.grok/skills/chain/`. See [CHAINS-CATALOG.md](CHAINS-CATALOG.md).

### 3.5 Loops

`LOOP.md`, `STATE.md`, `loop-budget.md`, `loop-run-log.md`, vault compound learning.  
Default L1 report-only.

### 3.6 MCP

`mcp-server/` + launchers `mcp-host-stdio.sh` / `mcp-ddev-stdio.sh`.  
**Develop only** — never public PaaS. Tools: manifest, cache reads, chains, wiki, audits.

### 3.7 Deploy / upgrade

- `scripts/deploy_grok_to_project.py` + `deploy-bundle.yaml` selections  
- CLI: `orchestrator upgrade` / `orchestrator init`  
- Bundle hash verify for high-risk paths  
- **No fleet wave** without `ORCHESTRATOR_WAVE_DEPLOY_APPROVED=1`

## 4. Engine modules (`scripts/_engine/`)

| Module | Responsibility |
|--------|----------------|
| `untrusted_text.py` | Injection / PII / toxic scrub |
| `vault.py` / `vault_query.py` / `vault_synthesis.py` | Hash-chained learning ledger |
| `session_envelope.py` | Session CTX minting |
| `platform_surface.py` | Host → directory map |
| `manifest_identity.py` | Not-template residue check |
| `mcp_runtime_policy.py` | Dev-only MCP + start options |
| `deploy.py` | Deploy/upgrade implementation |
| `contamination.py` | Template residue patterns |
| `ollama_detect.py` | Local LLM detection |
| `registry_compose.py` | Chain registry compose |
| `sync_grok.py` / `manifest_sync.py` | Platform sync |
| `app_compound.py` | Per-app compound gate |

## 5. Test layout

| Area | Tests |
|------|-------|
| Content guardrails | `tests/test_content_guardrails.py` |
| Platform surfaces / manifests | `tests/test_platform_*.py`, `test_manifest_sync.py` |
| Session envelope | `tests/test_session_context_envelope.py` |
| MCP / license | `mcp-server/tests/` |
| Deploy / CLI | `tests/test_deploy.py`, `test_cli_*.py` |
| Security lint | `test_malware_lint.py`, `test_session_security_sweep.py`, `test_skill_governance.py` |

Run:

```bash
export PYTHONPATH=scripts:src
python3 -m pytest tests -q
bash scripts/pre-release-gate.sh --skip-slow
```

## 6. Data flow (simplified)

```text
Operator
  → Host AI (Grok/Claude/Copilot/Cursor/Gemini)
      → Platform surface (.grok | .claude | .github | …)
      → scripts/ + MCP (optional)
      → docs/codebase cache + TODO + vault
      → (only after confirm) app source / git / deploy
```

## 7. See also

- [SECURITY-POSTURE.md](SECURITY-POSTURE.md)  
- [SKILLS-CATALOG.md](SKILLS-CATALOG.md)  
- [CHAINS-CATALOG.md](CHAINS-CATALOG.md)  
- Public spine: `docs/codebase/ARCHITECTURE.md`, `docs/codebase/STACK.md`  
