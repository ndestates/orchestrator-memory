# Template deploy

[UPDATED 2026-07-11]

## Overview

Push orchestrator `.grok` skills, prompts, agents, and root chains (`CHAIN.md`, `chains/registry.yaml`) to **one application repository at a time**. Optional selections copy `.claude/`, `.copilot/`, and `.github/` mirrors. Customized target files are never silently overwritten. Every deploy creates a rollback backup. The secure vault scaffolding (`reports/vault/events.jsonl` + synthesis) is deployed for self-building knowledge accumulation on targets.

**Operator runbook after a template release:** [Per-app upgrade](per-app-upgrade.md) (v1.4.0+).

### Default path (required)

| Action | Command |
|--------|---------|
| First install into an app | `orchestrator init /path/to/app --no-pr` |
| Update an app | `orchestrator upgrade /path/to/app --no-pr` |
| Wrapper script | `bash scripts/orchestrator-app-update.sh /path/to/app` |
| Check drift | `orchestrator status /path/to/app --json` |
| License gate | `orchestrator license` — see [Licensing](../reference/licensing.md) |

Full platform install (bootstrap this repo, Windows PowerShell, pip, npm): [Installation](../getting-started/installation.md).

### Fleet wave permanently removed

Multi-app fleet wave scripts and `orchestrator wave` are **deleted** (Phase A of the app-installable plan). There is no env override. Upgrade each app with the CLI only.

Historical records: [Wave deploy log](wave-deploy-log.md).

## Target projects (reference)

Each application repository is upgraded on its own. **Never blind-overwrite** an existing skill directory — local amendments win unless the operator opts in per file (skip / overwrite / merge).

Template deploys **generic** skill text; `customize-skills-for-project.py` applies the stack profile post-copy. Project-only skills on the target are preserved.

**Naming drift (reconcile before overwrite):** map legacy names where both exist — e.g. `scope-creep-detector` → `branch-context-agent`, `github-expert-agent` → `github-expert`.

### Path policy (maps to deploy script)

| Path class | Deploy behaviour | Rationale |
|------------|------------------|-----------|
| `.grok/skills/<name>/` | **skip** if customized or first-seen conflict; **add** if new | Protects amended skills |
| `.grok/prompts/`, `.grok/agents/` | Same conflict policy; review in deploy report | May be customized per project |
| `chains/`, `CHAIN.md` | Template copy; conflicts use skip/overwrite/merge | Chains are additive at registry level |
| `LOOP.md`, `STATE.md`, `loop-budget.md`, `loop-run-log.md` | In `loops` selection; never auto-deployed by default bundle | Project loop state is local |
| `scripts/chain-audit.sh`, `scripts/loop-audit.sh`, `scripts/sync_grok_to_github_claude.py`, `scripts/resume-branch.sh` | `scripts` selection | Shared tooling; resume-branch used by EOD + session-start |
| `.grok/skills/cache-freshness-check/` (incl. `scripts/cache_freshness_check.py`) | `grok` selection | Cache staleness check; pairs with session-start |
| `.github/workflows/*` | Not in default bundle; adopt per project | CI may differ by stack |
| `.github/project-manifest.yaml` (all platform copies) | **Never overwritten** by deploy/upgrade | Project-owned identity. **New projects:** `ensure_project_manifest` seeds a stack-aware file after profile resolve. **Template residue:** amends name/stack only. **Customized:** preserved as-is |
| `docs/codebase/`, `TODO/` | **Never deployed** | Project cache and work tracking |

After each deploy: `register-project-skills.py` registers project-only skills as `tier: app`, repairs stale alias paths, then `sync_grok_to_github_claude.py`, `check_name_alignment.py`, and `chain-audit.sh` on the target.

**Project-only skills (automatic):** before copying template skills, `detect-project-skills.py` scans the target repo:

- **Project-only** — skill dir on target but not in orchestrator template (e.g. `app-ops`) → kept, never overwritten
- **Customized** — same name as template but different `SKILL.md` (e.g. local `daily-standup`) → kept

No per-app preserve lists to maintain. After deploy, `register-project-skills.py` adds every local skill dir to `chains/registry.yaml` as `tier: app`.

### Branch policy (per-app)

Before upgrading an app, work from a **clean** checkout on a branch rooted on the latest remote tip (`git fetch` + `resume-branch.sh` / `remote_last`). Stale local checkouts are never used blindly.

```bash
# Per-app CLI only:
orchestrator upgrade /path/to/app --no-pr --dry-run
orchestrator upgrade /path/to/app --no-pr
```

## Before you begin

- Run from the **orchestrator** repository (source), not the target
- Target path absolute, e.g. `/path/to/app`
- For `claude`, `copilot`, or `github` selections: sync source first

  ```bash
  python3 scripts/sync_grok_to_github_claude.py
  ```

## Selections

```bash
python3 scripts/deploy_grok_to_project.py --list-selections
```

| Selection | Contents |
|-----------|----------|
| `grok` | `.grok/skills`, prompts, agents (default) |
| `chains` | `CHAIN.md`, `chains/registry.yaml` (default) |
| `loops` | `LOOP.md`, `loop-budget.md`, `patterns/` (default) |
| `scripts` | sync, audit, deploy scripts (default) |
| `claude` | `.claude/commands/`, `.claude/agents/`, `CLAUDE.md` |
| `copilot` | `.copilot/skills/` |
| `github` | `.github/skills/`, agents, prompts |

Default: `grok,chains,loops,scripts`. Use `--selections all` or comma-separated names.

## Steps

1. **Dry-run**

   ```bash
   python3 scripts/deploy_grok_to_project.py /path/to/target --dry-run
   python3 scripts/deploy_grok_to_project.py /path/to/target --dry-run --selections grok,claude,copilot
   ```

2. **Interactive deploy** (prompts on conflicts)

   ```bash
   python3 scripts/deploy_grok_to_project.py /path/to/target
   python3 scripts/deploy_grok_to_project.py /path/to/target --selections all
   ```

3. On conflict choose:
   - **skip** — keep project file (default)
   - **overwrite** — replace with template
   - **merge** — write `<file>.merged` with conflict markers
   - **diff** — show unified diff, then choose again

4. **On target after deploy**

   ```bash
   cd /path/to/target
   python3 scripts/sync_grok_to_github_claude.py
   python3 scripts/check_name_alignment.py
   bash scripts/chain-audit.sh
   ```

## Rollback

Backups live at `<target>/.grok/deploy-backups/<timestamp>/`.

```bash
# List backups
python3 scripts/deploy_grok_to_project.py /path/to/target --list-backups

# Restore latest
python3 scripts/deploy_grok_to_project.py /path/to/target --rollback

# Restore specific backup
python3 scripts/deploy_grok_to_project.py /path/to/target --rollback --backup-id 2026-06-17T143022Z

# Preview only
python3 scripts/deploy_grok_to_project.py /path/to/target --rollback --dry-run
```

Rollback restores pre-deploy files, removes files created during that deploy, and restores `deploy-state.json`.

## Chain invocation

```text
/chain template-deploy
```

Pass target path when prompted: `/orchestrator-deploy /path/to/app --selections grok,claude,copilot`

## Verify

- Target `.grok/deploy-state.json` updated
- Report in `.grok/deploy-reports/` includes `backup_id` and `selections`
- Backup directory created (unless `--no-backup`)
- `docs/codebase/` and manifests on target **not** touched

## Next steps

- [Chains and skills](chains-and-skills.md)
- [TEMPLATE_ADOPTION.md](../TEMPLATE_ADOPTION.md)
- [Operations testing](../operations/testing.md)

## Related

- [Guides index](index.md)