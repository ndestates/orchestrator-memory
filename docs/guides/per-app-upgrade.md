# Per-app upgrade (no fleet wave)

[UPDATED 2026-07-22] — Stable **v1.8.9**. Optional pre-release **v1.9.0-pre.5** (multi-workstream install fix; not Latest).

## Overview

After a new orchestrator release, **update each application repository yourself**, one at a time. Multi-app fleet wave deploy is **permanently removed** (not an env override).

| Do | Do not |
|----|--------|
| `orchestrator upgrade /path/to/app` | Reintroduce `deploy-*-wave.sh` or `orchestrator wave` |
| Dry-run first | Batch all apps in one unattended fleet script |
| Keep customized skills (skip policy) | Force-overwrite local amendments |

## Prerequisites

1. **Orchestrator template** at the release you want (stable: **v1.8.9**).  
   Multi-workstream **pre-release** (opt-in only): **v1.9.0-pre.5** — see [multi-workstream-prerelease.md](multi-workstream-prerelease.md).
2. **CLI** on your PATH (or module form).
3. Each **app** is a git repo. Prefer a **clean** working tree. Mid-feature WIP: pass **`--stash`**
   (`git stash push -u` → deploy → `stash pop`) instead of manual commit.
4. Optional: license gate only if `ORCHESTRATOR_LICENSE_URL` is set — see [Licensing](../reference/licensing.md).
5. After upgrade: run `bash scripts/ensure-mcp-host.sh` and `bash scripts/install-host-tools.sh --check` on the app — see [Multi-platform MCP and host tools](multi-platform-mcp-and-host-tools.md).

## Automatic checks (v1.4.2+; envelope-integrated ≥1.8.7)

You do **not** have to remember to run `status` every day. **Preferred automatic path:**

### 1. Session-start (recommended — fully automatic)

```text
/chain session-start
```

Every session-start mints the context envelope, which **always** runs
`session-orchestrator-check.py` and prints:

- `orch kind=… offer=yes|no installed=… available=…`
- When behind: `orch:` message + `orch_preview` / `orch_apply` lines  
  → agent offers **preview | apply | skip** (never auto-applies)

Works on the **lean** resume path too (no need for a full standup). In-app / **ddev**
need only the deployed `scripts/` tree (no global CLI required for the **check**).

| When | What happens |
|------|----------------|
| **`/chain session-start`** (preferred) | Envelope auto-check + offer; also standup Step 2 `--offer` on full path |
| Most CLI commands (`version`, `license`, …) | Auto-announces on **stderr** if cwd needs **init** or **upgrade** |
| `orchestrator check .` | Explicit check (exit **2** = upgrade, **3** = not installed) |
| In-app / **ddev** | `python3 scripts/session-orchestrator-check.py --offer` without pip install |

```bash
orchestrator check .
# orchestrator: upgrade available — installed 1.4.1, template 1.8.5 (…)
#   → preview: orchestrator upgrade . --if-available --no-pr
#   → apply:   orchestrator upgrade . --if-available --yes --no-pr
```

### Check then upgrade (local / per-app)

| Goal | Command |
|------|---------|
| Detect only | `orchestrator check .` or `python3 scripts/session-orchestrator-check.py --offer` |
| Preview upgrade if behind | `orchestrator upgrade . --if-available --no-pr` (dry-run without `--yes`) |
| Apply upgrade if behind (local CLI template) | `orchestrator upgrade . --if-available --yes --no-pr` |
| **From GitHub release (latest)** | `orchestrator upgrade . --from-github --yes --no-pr` |
| **From GitHub release (tag)** | `orchestrator upgrade . --from-github v1.8.9 --yes --no-pr` |
| **Agent-safe (quiet summary only)** | `orchestrator upgrade . --from-github v1.9.6 --yes --no-pr --quiet` |
| **Dirty app WIP (auto stash -u)** | `orchestrator upgrade . --from-github v1.9.6 --yes --no-pr --quiet --stash` |
| **Pre-release multi-workstream (worktrees/prompts)** | `orchestrator upgrade . --from-github v1.9.0-pre.5 --yes --no-pr` (not stable) |
| Check + fetch GitHub if behind | `orchestrator upgrade . --if-available --from-github --yes --no-pr` |
| Session-start interactive | `python3 scripts/session-orchestrator-check.py --prompt` (TTY asks y/N) |

`--from-github` clones/downloads the release into `~/.cache/orchestrator/releases/<ver>` (override with `ORCHESTRATOR_CACHE`) and uses it as the template root — **no sibling monorepo required**. Without `--yes`, GitHub upgrades stay **dry-run**.

**Version sources (best of):** local CLI/`VERSION`, app stamp `scripts/orchestrator-template-version`, sibling `../orchestrator/VERSION`, env `ORCHESTRATOR_TEMPLATE_VERSION`, and **GitHub Releases latest** (`ORCHESTRATOR_GITHUB_REPO`, default `ndestates/orchestrator`). Private repos need `GITHUB_TOKEN` or `GH_TOKEN`. Disable network probe: `ORCHESTRATOR_NO_REMOTE_VERSION=1`.

Opt out of auto-announce: `export ORCHESTRATOR_NO_UPDATE_CHECK=1`.

Works inside **ddev** (no `pip install orchestrator` required). Host-side `orchestrator check`
still uses the full CLI package when comparing against a newer template checkout.  
**Apply still needs a host CLI** whose template root is at least the target version (or a sibling orchestrator checkout).


## Step 1 — Get release v1.4.2 of orchestrator

### A. From git (recommended while developing)

```bash
cd /path/to/orchestrator   # e.g. ~/projects/orchestrator
git fetch origin --tags
git checkout master        # or develop once v1.4.2 is merged
git pull --ff-only
git checkout v1.4.2        # annotated release tag when published
# or stay on master after the release merge

# Install / refresh CLI from this checkout
bash scripts/install.sh --cli
# Windows PowerShell:
#   .\scripts\install.ps1 -Cli
# optional npm wrapper:
#   bash scripts/install.sh --npm

orchestrator version
# expect: orchestrator 1.4.2 (template 1.4.2, …)
```

### B. From GitHub Release wheel (when the release is published)

```bash
# Download orchestrator-*.whl from:
#   https://github.com/ndestates/orchestrator/releases/tag/v1.4.2
python3 -m pip install --upgrade /path/to/orchestrator-1.4.2-*.whl

orchestrator version
```

### C. npm wrapper (optional)

```bash
# From the v1.4.2 checkout:
npm install -g .
# When the scoped package is published to npm:
# npm install -g @ndestates/orchestrator@1.4.2
```

The npm bin is a thin shim; the real CLI is still Python.

## Step 2 — Check drift on one app

```bash
orchestrator status /path/to/your-app --json
# human:
orchestrator status /path/to/your-app
```

Note installed template version vs available `1.4.2`.

## Step 3 — Dry-run upgrade

Always plan first:

```bash
cd /path/to/orchestrator

orchestrator upgrade /path/to/your-app --no-pr --dry-run
# equivalent wrapper:
# bash scripts/orchestrator-app-update.sh /path/to/your-app --dry-run --no-pr
```

Review the report: new files, skips (customized), conflicts. Default selections: `grok`, `chains`, `loops`, `scripts` (see `scripts/deploy-bundle.yaml`).

Useful flags:

| Flag | Purpose |
|------|---------|
| `--dry-run` | No writes |
| `--no-pr` | Commit on a feature branch without opening a GitHub PR |
| `--to 1.4.2` | Pin target template version (optional if checkout is already 1.4.2) |
| `--selections grok,chains,scripts` | Narrow bundle (comma list) |
| `--profile laravel` | Stack profile when applicable |

## Step 4 — Apply upgrade

```bash
# working tree of the app must be clean
orchestrator upgrade /path/to/your-app --no-pr
```

Typical result:

- Feature branch on the **app**
- Template surfaces copied with skip/overwrite/merge policy
- Project-only and customized skills **kept**
- Backup under `.grok/deploy-backups/…`
- Lock file updated to template version **1.4.2**

Then on the **app** repo:

```bash
cd /path/to/your-app
git status
# review, push, open PR as you normally do for that product
git push -u origin HEAD
```

## Step 5 — Post-upgrade checks (on the app)

```bash
cd /path/to/your-app

# Host MCP + ripgrep (v1.8.8+) — scripts or CLI
bash scripts/ensure-mcp-host.sh --check || bash scripts/ensure-mcp-host.sh
bash scripts/install-host-tools.sh --check || bash scripts/install-host-tools.sh --yes
# equivalent: orchestrator ensure --check || orchestrator ensure --yes
# if host CLI itself is stale: orchestrator self-upgrade --to 1.9.5 --yes

# vault brief (if scripts selection deployed)
python3 scripts/session-vault-brief.py 2>/dev/null || echo "vault brief not present yet — ok on first vault bootstrap"

# chain registry
bash scripts/chain-audit.sh 2>/dev/null || true

# session (any host)
python3 scripts/session-context-envelope.py --write
# In Grok/Claude: /chain session-start — expect mcp_ready=yes when mcp-server present
```

Enable the client MCP file for your host (`.grok/config.toml`, `.cursor/mcp.json`, `.chatgpt/mcp.chatgpt.example.json`, etc.) — [production guide](multi-platform-mcp-and-host-tools.md).

**v1.4.2 brings (among other things):**

- **Patch:** reliable `init`/`upgrade` when CLI uses the template on `PYTHONPATH` (sync root pin)
- Session-start **vault brain brief** (`scripts/session-vault-brief.py`) — not only branch pointer
- Vault helper scripts in the **scripts** deploy selection
- npm package surface for the CLI wrapper
- Installer/docs alignment: per-app only; fleet deprecated

## Repeat per app

Run steps 2–5 for each product. Example list (adjust paths):

```text
~/projects/e-ndsign
~/projects/ndestates-io
~/projects/lightstone
~/projects/jerseyhouseprices
~/projects/mailchimp
~/projects/facebook-stats
~/projects/google-stats
~/projects/ndestates
```

There is **no** supported “upgrade all” command for routine use.

## What is protected

- Project-only skills (exist only on the app)
- Customized skills (same name as template, different content)
- `docs/codebase/`, `TODO/` — never deployed
- App-owned `chains/registry.app.yaml` (when split)

Details: [Template deploy](template-deploy.md).

## Fleet wave (removed)

Fleet scripts and `orchestrator wave` are **deleted**. There is no
`ORCHESTRATOR_WAVE_DEPLOY_APPROVED` override. Document each app upgrade in that
app’s PR / TODO. Historical notes: [Wave deploy log](wave-deploy-log.md).

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `working tree is not clean` | Commit or stash on the app, retry |
| `license check failed` | See [Licensing](../reference/licensing.md); unset URL for local fail-open |
| CLI version old | Re-run `bash scripts/install.sh --cli` from the v1.4.2 checkout |
| Missing `session-vault-brief.py` on app | Re-run upgrade with default selections (includes `scripts`) |
| Want only skills, not scripts | `--selections grok,chains` then add `scripts` later |

## Related

- [Installation](../getting-started/installation.md) — bootstrap + package paths
- [Template deploy](template-deploy.md) — policy and inventory notes
- [Wave deploy log](wave-deploy-log.md) — historical fleet only
- Releases: <https://github.com/ndestates/orchestrator/releases>
