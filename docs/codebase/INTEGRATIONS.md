# Integrations

[UPDATED 2026-07-09]

Lens: Operator, Security

## GitHub

| Integration | Path / command |
|-------------|----------------|
| Actions workflows | `.github/workflows/*.yml` (10) |
| Branch protection | `develop`, `master` — PR required |
| Promotion PRs | `branch-promotion-prs.yml` — auto draft PRs |
| Dependabot | `.github/dependabot.yml` |
| CLI | `gh pr`, `gh run`, `gh workflow` for triage/dispatch |

### Workflow Summary

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `release.yml` | tag `v*` / manual | Release automation (version, prerelease, draft inputs) |
| `repository-sync.yml` | daily 09:00 UTC / dispatch | Branch fetch + divergence reports |
| `loop-daily-triage.yml` | weekdays 09:00 UTC | L1 triage readiness (host snapshot) |
| `loop-weekly-watch.yml` | Mon 09:30 UTC / dispatch | L1 watches (cache-freshness, chain-health, github-ci, repo-health) |
| `run-chain.yml` | workflow_dispatch | One-click chain trigger; runs `run-chain-host.sh` + dispatch note |
| `branch-promotion-prs.yml` | push `feature/**`, `develop` | Promotion PR creation |
| `chain-audit.yml` | PR/push `develop`, `feature/**` | Chain registry validation |
| `mcp-security.yml` | PR/push touching `mcp-server/**` | MCP tests (sandbox/auth/gate) + threat scan |

All workflows pin Node 24 (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`) and verify via `scripts/verify_github_actions_node24.py`.

### Required Repo Settings

- **Workflow permissions:** Read and write
- **Allow Actions to create/approve PRs:** enabled (for promotion workflow)

## MCP Server

| Aspect | Detail |
|--------|--------|
| Package | `orchestrator-mcp` (`mcp-server/`) |
| Transports | `stdio` (local, no key) · `streamable-http` (API key) |
| Auth env | `ORCHESTRATOR_MCP_API_KEY` (HTTP only) |
| Sandbox | reads confined to `PROJECT_ROOT`; `ORCHESTRATOR_MCP_MAX_READ_BYTES` (64KB default) |
| Audit | append-only JSONL → `reports/mcp/` (`ORCHESTRATOR_MCP_AUDIT_DIR`) |
| Clients | Cursor (`mcp.cursor*.json`), Grok (`mcp.grok.project.example.toml`), HTTP (`mcp.http.example.json`) |
| DDEV (app repos) | `mcp-server/ddev/Dockerfile.mcp` + `ddev.config.snippet.yaml` |
| Deploy | `scripts/deploy-mcp-wave.sh` or `deploy_grok_to_project.py --selections mcp` |
| Threat scan | `bash scripts/mcp-threat-scan.sh` |

## Sync Targets (from `.grok/`)

| Source | Destination |
|--------|-------------|
| `.grok/skills/` | `.github/skills/`, `.copilot/skills/`, `.claude/commands/` |
| `.grok/prompts/` | `.github/prompts/`, `.claude/commands/` |
| `.grok/agents/` | `.github/agents/`, `.claude/agents/` |
| copilot-instructions skill | `.github/copilot-instructions.md` |

Command: `python3 scripts/sync_grok_to_github_claude.py`

## Template Deploy (to app repos)

| Mechanism | Command |
|-----------|---------|
| **Preferred: per-app CLI** | `orchestrator init/upgrade <path>` or `bash scripts/orchestrator-app-update.sh <path>` |
| Bootstrap template repo | `bash scripts/install.sh [--cli]` · Windows: `.\scripts\install.ps1 [-Cli]` |
| Single repo, low-level deploy | `python3 scripts/deploy_grok_to_project.py <path> --selections <bundles>` |
| Fleet (wave) — **manual only** | Blocked unless `ORCHESTRATOR_WAVE_DEPLOY_APPROVED=1`; see `wave-deploy-policy.sh` |
| Stack overrides | `scripts/stack-profiles/{laravel,python-flask,google-stats,facebook-stats}.yaml` via `manifest-map.yaml` |
| Skill detect/customize | `scripts/detect-project-skills.py`, `customize-skills-for-project.py` |
| Human docs | `docs/getting-started/installation.md`, `docs/reference/licensing.md`, `docs/guides/template-deploy.md` |

## Downstream Template Skills (active only when forked to app repos)

Skills reference integrations for target projects — **not active in this template repo**:
`digitalocean-deploy`, `amazon-ses-email`, `aws-route53-dns`, `paypal-billing`, `didit-identity-integration`, `loqate-address-integration`, `ddev-local-runtime`, `laravel-expert`, `mysql-database-expert`.

Each vendor skill uses **three layers:** `SKILL.md` (orchestration) · `references/*-api-canonical.md` (ground truth) · `exports/*-integration-prompt.md` (copy-paste).

### App vendor map (`ndestates-io` / `e-ndsign`)

| Vendor | Skill | e-ndsign | ndestates-io | Wired in app code |
|--------|-------|----------|--------------|-------------------|
| PayPal | `paypal-billing-integration` | Planned (skills) | Demo routes + License model | Partial (ndestates-io env only) |
| Amazon SES | `amazon-ses-email` | Planned | Planned | No |
| AWS Route53 | `aws-route53-dns` | Planned | Planned | No |
| DigitalOcean | `digitalocean-app-platform-docr-deploy` | Planned | Planned | DDEV local |
| **Didit** | `didit-identity-integration` | Signer KYC/re-auth | Optional KYB | Skill scaffold only |
| **Loqate** | `loqate-address-integration` | Signer address | Checkout address | Skill scaffold only |

## Evidence

- `.github/workflows/*.yml`, `.github/dependabot.yml`
- `mcp-server/README.md`, `mcp-server/config/*`, `mcp-server/ddev/Dockerfile.mcp`
- `scripts/sync_grok_to_github_claude.py`, `scripts/deploy_grok_to_project.py`, `scripts/wave-inventory.yaml`, `scripts/stack-profiles/`
- `docs/codebase/.codebase-scan.txt` (`=== CI/CD WORKFLOWS ===`)
