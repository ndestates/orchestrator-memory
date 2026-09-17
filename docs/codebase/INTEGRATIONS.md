# Integrations

[UPDATED 2026-09-17] — public `product-release.yml`; factory workflows not in this tree.

> Lens: Operator, Security — evidence from `.github/workflows/`, `mcp-server/`, `package.json`, `services/license-api/README.md`.

## GitHub

| Integration | Path / command |
|-------------|----------------|
| Actions | Public: `.github/workflows/product-release.yml`. Factory suite stays private. |
| Branch protection | `develop`, `master` — PR required |
| Promotion PRs | `branch-promotion-prs.yml` |
| Dependabot | `.github/dependabot.yml` |
| CLI | `gh pr`, `gh run`, `gh workflow` |
| Packages | npmjs `@ndestates/orchestrator` (optional `NPM_TOKEN`); matching wheel on GitHub Release |
| Releases | tag `v*` → wheel + sdist + VSIX |

### Workflow summary

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `product-release.yml` | tag `v*` / dispatch | Public wheel + sdist + VSIX (no factory pre-release gate) |
| `release.yml` | tag `v*` / dispatch | Private factory gate (full pytest + security) |
| `vscode-marketplace.yml` | tag `v*` / dispatch | Package VSIX; Marketplace publish **optional** (`VSCE_PAT`) |
| `tooling-tests.yml` | PR/push on scripts/tests | `pytest tests` + malware + threat + governance + chain-audit |
| `chain-audit.yml` | PR/push `develop`, `feature/**` | Registry 100/100 |
| `mcp-security.yml` | `mcp-server/**` | MCP pytest + threat scan |
| `security-malware.yml` | PR/push | Malware lint |
| `template-decontamination.yml` | PR/push | Fork residue gate |
| `loop-daily-triage.yml` | weekdays 09:00 UTC | L1 host snapshot |
| `loop-weekly-watch.yml` | Mon 09:30 UTC | L1 watch snapshots |
| `run-chain.yml` | `workflow_dispatch` | `run-chain-host.sh` |
| `branch-promotion-prs.yml` | push `feature/**`, `develop` | Draft promotion PRs |
| `repository-sync.yml` | daily 09:00 UTC | Branch fetch + divergence |

All pin Node 24 (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`).

### Required repo settings

- Workflow permissions: Read and write
- Allow Actions to create/approve PRs (promotion)
- Optional secret `VSCE_PAT` — not required to ship; human Marketplace upload is the default path

## VS Code Marketplace

- Item: `ndestates.orchestrator-memory`
- Manage: `https://marketplace.visualstudio.com/manage/publishers/ndestates`
- CI packages VSIX; default is **human upload** (workflow comment: never fail solely because `VSCE_PAT` is missing)

## MCP Server

| Aspect | Detail |
|--------|--------|
| Package | `orchestrator-mcp` 0.1.0 (`mcp-server/`) |
| Transports | `stdio` (local, no key) · `streamable-http` (API key) |
| Auth env | `ORCHESTRATOR_MCP_API_KEY` (HTTP) |
| Sandbox | `PROJECT_ROOT`; `ORCHESTRATOR_MCP_MAX_READ_BYTES` (64KB default) |
| Audit | `reports/mcp/` (`ORCHESTRATOR_MCP_AUDIT_DIR`) |
| Policy | `runtime.mcp: off` default; `dev_only` — never public hosts |
| Clients | Live `.grok/config.toml` + `.cursor/mcp.json` **disabled**. Opt-in examples under `mcp-server/config/` |

## Memory and vault

| Store | Path | Role |
|-------|------|------|
| SQLite runtime | `reports/memory/memory.db` (gitignored) | Session briefs / query |
| Vault ledger | `reports/vault/events.jsonl` | Durable hashed lessons |
| Inbox | `reports/memory/inbox/` | Drop files for ingest |

Guide: `docs/guides/always-on-memory.md`. Dual-write when `memory_policy.dual_write_vault: true`.

## Optional license API

Public product is **Apache-2.0 freeware**. `services/license-api/` is **not** required for end users. Gates fail-open when `ORCHESTRATOR_LICENSE_URL` is unset. Env names only: `ORCHESTRATOR_LICENSE_URL`, `ORCHESTRATOR_LICENSE_KEY`, `ORCHESTRATOR_LICENSE_DB`, `ORCHESTRATOR_LICENSE_ADMIN_TOKEN`.

## Sync targets (from `.grok/`)

| Source | Destination |
|--------|-------------|
| `.grok/skills/` | `.github/skills/`, `.copilot/skills/`, `.claude/commands/` |
| `.grok/prompts/` | `.github/prompts/`, `.claude/commands/` |
| `.grok/agents/` | `.github/agents/`, `.claude/agents/` |
| copilot-instructions skill | `.github/copilot-instructions.md` |
| `.github/project-manifest.yaml` | per-platform manifests via `sync_manifests.py` |

Command: `python3 scripts/sync_grok_to_github_claude.py`

## Template deploy (to app repos)

| Mechanism | Command |
|-----------|---------|
| Preferred CLI | `orchestrator init` / `upgrade` |
| Wrapper | `bash scripts/orchestrator-app-update.sh <path>` |
| Bootstrap | `bash scripts/install.sh [--cli]` · `.\scripts\install.ps1 [-Cli]` |
| Low-level | `python3 scripts/deploy_grok_to_project.py <path> --selections …` |
| Fleet wave | **Deleted** — do not reintroduce |

## Downstream vendor skills (app repos only)

Not active in this template: DigitalOcean, SES, Route53, PayPal, Didit, Loqate, DDEV, Laravel/MySQL experts. Three layers: `SKILL.md` · `references/*-api-canonical.md` · `exports/*-integration-prompt.md`.

## Evidence

- `.github/workflows/*.yml` (13 names from scan + `ls`)
- `mcp-server/pyproject.toml`, `mcp-server/README.md`
- `extensions/vscode-orchestrator/package.json`, `vscode-marketplace.yml` header
- `services/license-api/README.md`
- `tests/test_wave_absent.py`
- `docs/guides/always-on-memory.md`
