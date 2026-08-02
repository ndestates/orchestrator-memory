# Structure

[UPDATED 2026-07-07] — aligned with full docs update. See getting-started/project-overview.md and reference/index.md.

## Top-Level Layout

```
.
├── .grok/                  # Grok-native skills, prompts, agents, memories (SOURCE OF TRUTH)
├── .github/                # Copilot: skills, prompts, agents, workflows, manifest, dependabot
├── .claude/                # Claude Code: commands, agents, manifest
├── .copilot/               # Copilot memories + mirrored skills
├── .cursor/                # Cursor config surface
├── mcp-server/             # Python MCP server (orchestrator-mcp)
├── chains/                 # chains/registry.yaml (machine chain catalog)
├── patterns/               # Loop + on-demand patterns + registry.yaml
├── starters/               # Loop starter templates (e.g. daily-triage/)
├── docs/                   # Human docs (index, guides, reference, operations) + codebase cache
│   └── codebase/           # This cache (lean context). Cross-links: guides/knowledge-vault.md, etc. See getting-started/project-overview.md.
├── TODO/                   # Daily task files (YYYY-MM-DD_TODO.md)
├── reports/                # loops, chains, changelog, bugs, security, research, tokens, mcp
├── scripts/                # sync, audits, install, wave-deploy, stack-profiles
├── LOOP.md, STATE.md       # Loop registry + durable state
├── CHAIN.md                # Chain registry (human)
├── CHANGELOG.md            # Release changelog
├── loop-budget.md          # Token budgets per loop
└── loop-run-log.md         # Append-only loop history
```

## `.grok/` (primary — source of truth)

| Path | Count / notes |
|------|----------------|
| `skills/*/SKILL.md` | 46 skills incl. `chain`, `loop-triage`, `cache-efficient`, `github-workflow-expert`, `changelog-specialist` |
| `prompts/*.md` | 10 prompts (load-cache, standup, read-codebase, orchestrator, etc.) |
| `agents/*.md` | 16 specialist agents |
| `memories/INDEX.md` | Memory routing (tier 1/2) |

## `.github/`

| Path | Purpose |
|------|---------|
| `project-manifest.yaml` | Stack, paths, token/loop/chain policy |
| `skills/` (45), `prompts/`, `agents/` | Copilot surfaces (synced from `.grok/`) |
| `workflows/` | 10 workflows (see INTEGRATIONS.md) |
| `copilot-instructions.md` | Repo AI rules (synced from copilot-instructions skill) |
| `dependabot.yml` | Dependency updates |

## `.claude/`

| Path | Purpose |
|------|---------|
| `commands/*.md` (48) | Slash commands (synced from skills + prompts) |
| `agents/*.md` (19) | Subagents with YAML frontmatter |
| `project-manifest.yaml` | Mirror of `.github/project-manifest.yaml` |

## `mcp-server/`

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata (`orchestrator-mcp`) |
| `src/orchestrator_mcp/` | `server.py`, `auth.py`, `audit.py`, `config.py`, `helpers.py`, `sandbox.py` |
| `config/` | Client config examples (Cursor, Grok, HTTP, DDEV snippet) |
| `ddev/Dockerfile.mcp` | DDEV web-image build for app repos |
| `tests/test_helpers.py` | Helper unit tests |

## `scripts/` (34 files)

| Group | Examples | Purpose |
|-------|----------|---------|
| Sync | `sync_grok_to_github_claude.py` | `.grok/` → `.github/` + `.claude/` + `.copilot/` |
| Audits | `chain-audit.sh`, `loop-audit.sh`, `check_name_alignment.py`, `verify_github_actions_node24.py`, `mcp-threat-scan.sh` | Registry/policy/security validation |
| Deploy | `deploy_grok_to_project.py`, `detect-project-skills.py`, `customize-skills-for-project.py`, `deploy-bundle.yaml` | Template deploy to app repos |
| Wave | `wave-apps.sh`, `wave-inventory.yaml`, `wave-app-branch.sh`, `resolve-wave-app-path.py`, `deploy-*-wave.sh`, `commit-*-wave.sh`, `fix-*-wave.sh` | Multi-app fleet deploy/commit |
| Loop host | `loop-*-host.sh`, `chain-completion-write.sh`, `run-chain-host.sh` | Scheduled snapshots + chain completion |
| `stack-profiles/` | `laravel.yaml`, `python-flask.yaml`, `google-stats.yaml`, `facebook-stats.yaml`, `manifest-map.yaml` | Per-stack manifest/skill overrides for deploy |

## `patterns/`

| File | Type |
|------|------|
| `daily-triage.md` | L1 scheduled loop |
| `cache-freshness-watch.md`, `chain-health-watch.md`, `github-ci-watch.md`, `repo-health-watch.md` | Weekly L1 watches |
| `perspective-guided-discovery.md` | On-demand pattern |
| `registry.yaml` | Machine catalog (`loops:` + `patterns:`) |

## Evidence

- `docs/codebase/.codebase-scan.txt` (`=== TREE ===`, generated 2026-06-23)
- `ls` over `.grok/`, `.claude/`, `.github/`, `scripts/`, `scripts/stack-profiles/`, `patterns/`, `mcp-server/`, `reports/`
- `mcp-server/README.md`
