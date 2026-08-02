# Installation

[UPDATED 2026-08-02] — package-first host CLI · **v2.2.0** wheel · production ship guide · **BYOK**

## Bring your own keys (required)

Orchestrator does **not** include model-provider API keys or free cloud model access.

| You need | Examples |
|----------|----------|
| **Your own AI host account** | Claude Code, Grok Build, GitHub Copilot, Cursor, Gemini, ChatGPT |
| **Your own API keys** (when using APIs) | Created in **your** OpenAI / Anthropic / xAI / Google / etc. console |
| **Local option (no cloud key)** | [Ollama BYOM](../guides/local-ollama.md) if you prefer models on your machine |

Do **not** commit keys. Details: [Bring your own keys](../reference/bring-your-own-keys.md).

## Overview

Two different installs — do not mix them up:

| Layer | What | Lives where | Survives `git checkout`? |
|-------|------|-------------|---------------------------|
| **Host package** | `orchestrator` CLI on PATH | Machine (uv tool / pip / npm) | **Yes** — not in any repo branch |
| **In-app template** | skills, chains, scripts, lock | Inside **one app git repo** | Only if that branch has those commits (or project-global sync) |

**Want the tool on every branch, every repo?** Install the **host package** once.  
**Want skills/session scripts inside a product app?** Then `init` / `upgrade` that app (git-tracked).

**Fleet wave deploy is permanently removed.** Use `orchestrator init` / `orchestrator upgrade` per app only.

## Host package first (recommended — persists across branches)

**Always-on memory (any project, no per-app deploy required):** after the host CLI is installed:

```bash
orchestrator memory brief --seed
orchestrator memory query "what should I work on?"
```

Full guide: [Host-first memory](../guides/host-first-memory.md) · VS Code: `extensions/vscode-orchestrator/`.  
**Ship to production (npm / pip / VSIX / tag):** [Production ship](../guides/production-ship.md).



The CLI is a normal **Python package** (`orchestrator` on PyPI-style path) or **npm wrapper** (`@ndestates/orchestrator` → Python). It is **not** checked out with your feature branch.

### Preferred: uv tool (Python)

Isolated install under `~/.local/share/uv/tools/orchestrator`; binary on `~/.local/bin`.

```bash
# Preferred production: GitHub Release wheel (no clone required)
VER=2.2.0
uv tool install --force \
  "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"

# From a checkout of this repo (any branch — install is not tied to it after this)
cd /path/to/orchestrator
bash scripts/install.sh --uv-tool
# equivalent:
# uv tool install --force --from . orchestrator

# Verify (run from any directory / any app branch)
orchestrator version
# → orchestrator 2.2.0 (template 2.2.0, installed)

# Later refresh (same idea as npm -g update)
orchestrator self-upgrade --yes
# or re-run the uv tool install line above
```

Ensure `~/.local/bin` is on `PATH`.

### Alternative: pip (Python)

```bash
VER=2.2.0
pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
# or from a clone: bash scripts/install.sh --cli
# or: python3 -m pip install -e .
# PyPI (when published): pip install orchestrator==2.2.0
```

### Alternative: npm or pnpm (Node wrapper → Python CLI)

Same host package (`@ndestates/orchestrator`); pick the manager you already use. Postinstall installs/refreshes the **Python** CLI. Machine-global — not tied to git branches.

```bash
cd /path/to/orchestrator
# npm
bash scripts/install.sh --npm
# or: npm install -g .

# pnpm (if that is your Node package manager)
bash scripts/install.sh --pnpm
# or: pnpm add -g .

# auto: pnpm if on PATH, else npm
bash scripts/install.sh --node

# Production (GitHub Packages — default after v2.0.0+):
#   echo '@ndestates:registry=https://npm.pkg.github.com' >> ~/.npmrc
#   echo '//npm.pkg.github.com/:_authToken=YOUR_GH_PAT' >> ~/.npmrc   # read:packages
#   npm install -g @ndestates/orchestrator
# Optional npmjs.org (if we also publish there):
#   npm install -g @ndestates/orchestrator
```

Node **latest LTS** recommended. Ensure the manager’s global `bin` is on `PATH` (`npm bin -g` / `pnpm bin -g`).  
Full ship notes: [Production ship](../guides/production-ship.md) (GitHub Packages vs npmjs).

### Uninstall host package only

```bash
orchestrator uninstall --host --no-project --apply --yes
# or: uv tool uninstall orchestrator
# or: npm uninstall -g @ndestates/orchestrator
# or: pnpm remove -g @ndestates/orchestrator
```

---

## Before you begin

- **Git** installed and available on `PATH`
- **Python 3.10+** (`python3` on Linux/macOS, `python` on Windows)
- **uv** recommended for host package (no system `pip` required)
- **ripgrep (`rg`)** — recommended host tool for Cyber Essentials session scans and agent search (see [Host tools (ripgrep)](#host-tools-ripgrep))
- Network access if you will enforce licensing (optional; see [Licensing](../reference/licensing.md))
- A target application git repository for per-app install (clean working tree)

## Choose your path

| Goal | Tool | Platform |
|------|------|----------|
| **Host CLI package (branch-independent)** | `bash scripts/install.sh --uv-tool` (preferred) · `--cli` · `--npm` · `--pnpm` · `--node` | All |
| Bootstrap **this** template repo after clone | `scripts/install.sh` or `scripts/install.ps1` | Linux/macOS / Windows |
| Install via **npm/pnpm** (Node wrapper → Python CLI) | `npm install -g .` / `pnpm add -g .` or `--npm` / `--pnpm` / `--node` | All (Node 18+) |
| Host tools + MCP ready | `bash scripts/install.sh --host-tools --mcp` | Linux/macOS / WSL |
| First-time **template files** into **one app repo** | `orchestrator init <path>` | All |
| Update template files in **one app repo** | `orchestrator upgrade <path>` | All |
| Multi-platform surfaces (incl. **ChatGPT**) | See [platform-surfaces.md](../reference/platform-surfaces.md) · MCP: [multi-platform-tool-use.md](../reference/tools/multi-platform-tool-use.md) | All hosts |

---

## Steps — Linux and macOS

### 1. Clone the template

```bash
git clone https://github.com/ndestates/orchestrator.git
cd orchestrator
```

### 2. Bootstrap the repository

```bash
bash scripts/install.sh
```

Optional: install the **host CLI package** (persists across branches — preferred):

```bash
# Preferred (uv tool — no system pip required):
bash scripts/install.sh --uv-tool

# pip editable (needs pip):
bash scripts/install.sh --cli
# equivalent: python3 -m pip install -e .

# npm wrapper (Node 18+; postinstall installs Python CLI):
bash scripts/install.sh --npm
# equivalent: npm install -g .

# optional local Ollama (BYOM — not required for cloud AI):
bash scripts/install.sh --ollama
# or: bash scripts/install-ollama.sh
# see docs/guides/local-ollama.md

# host tools: ripgrep (rg) for CSE / session-security-sweep
bash scripts/install.sh --host-tools
# or: bash scripts/install-host-tools.sh --yes

# host MCP stdio (orchestrator-host) — ready for Grok/Cursor session-start
bash scripts/install.sh --mcp
# or: bash scripts/ensure-mcp-host.sh
```

### 3. Verify CLI

```bash
orchestrator version
# or without PATH install:
PYTHONPATH=src python3 -m orchestrator_cli version
```

### 4. Install into one application repo

```bash
orchestrator init /path/to/your-app --no-pr --dry-run   # plan first
orchestrator init /path/to/your-app --no-pr             # apply
orchestrator status /path/to/your-app --json
```

Update later:

```bash
orchestrator upgrade /path/to/your-app --no-pr
# wrapper:
bash scripts/orchestrator-app-update.sh /path/to/your-app --no-pr

# Check then upgrade (safe default = dry-run without --yes):
orchestrator check /path/to/your-app
orchestrator upgrade /path/to/your-app --if-available --no-pr          # preview (local CLI)
orchestrator upgrade /path/to/your-app --if-available --yes --no-pr     # apply (local CLI)

# From GitHub Releases (no monorepo sibling needed; private: GITHUB_TOKEN):
orchestrator upgrade /path/to/your-app --from-github --yes --no-pr
orchestrator upgrade /path/to/your-app --from-github v1.8.5 --yes --no-pr
```

Session-start in the app runs `python3 scripts/session-orchestrator-check.py --offer` and should **offer** preview/apply/skip (never auto-apply without confirmation). See [Per-app upgrade](../guides/per-app-upgrade.md).

---

## Host tools (ripgrep)

**Why:** Session-start runs `scripts/session-security-sweep.sh` → Cyber Essentials lean scan. Without **`rg` (ripgrep)**, several controls print `(rg not available — skipped)` and miss real findings. Agents also rely on fast search for cache-first workflows.

**Project installer (preferred on host / WSL):**

```bash
bash scripts/install-host-tools.sh --check   # status only (exit 1 if missing)
bash scripts/install-host-tools.sh --yes     # install via apt/dnf/brew/…
# or via bootstrap:
bash scripts/install.sh --host-tools
```

| Environment | How to install `rg` |
|-------------|---------------------|
| **Debian / Ubuntu / WSL2** (recommended on WSL) | `sudo apt-get update && sudo apt-get install -y ripgrep` or `bash scripts/install-host-tools.sh --yes` |
| **Fedora / RHEL** | `sudo dnf install -y ripgrep` |
| **Arch** | `sudo pacman -S ripgrep` |
| **macOS** | `brew install ripgrep` |
| **Windows host** | `.\scripts\install-host-tools.ps1 -Yes` (winget/choco/scoop) or `.\scripts\install.ps1 -HostTools` |
| **Windows + WSL** | Install **inside WSL** (orchestrator bash scripts run there): `wsl -e bash -lc 'sudo apt-get install -y ripgrep'` |
| **DDEV web** (Laravel/PHP apps) | Prefer config: `webimage_extra_packages: [ripgrep]` in `.ddev/config.yaml`, then `ddev restart`. Snippet: `mcp-server/ddev/webimage-extra-packages.snippet.yaml`. Dockerfile layer: copy `mcp-server/ddev/Dockerfile.tools` → `.ddev/web-build/Dockerfile.tools`. MCP image also installs ripgrep (`Dockerfile.mcp`). |
| **Docker image** | `RUN apt-get update && apt-get install -y --no-install-recommends ripgrep && rm -rf /var/lib/apt/lists/*` |
| **CI (this repo)** | Tooling Tests workflow installs `ripgrep` on the runner |

Verify:

```bash
rg --version
bash scripts/install-host-tools.sh --check
# DDEV:
ddev exec rg --version
```

`install.sh` **warns** when `rg` is missing but does not fail the bootstrap (no silent `sudo`). Pass `--host-tools` to attempt install non-interactively.

### Host MCP (stdio) — ready from session-start

| Piece | Role |
|-------|------|
| `scripts/ensure-mcp-host.sh` | Build/repair `mcp-server/.venv` (uv preferred; else `python3-venv`) |
| `scripts/mcp-host-stdio.sh` | Grok/Cursor launcher — ensure then `orchestrator-mcp --transport stdio` |
| `detect-project-runtime.sh` | **Auto-repairs** host MCP on session-start so `mcp_ready=yes` |
| `.grok/config.toml` | `orchestrator-host` → `args = ["scripts/mcp-host-stdio.sh"]` |

```bash
bash scripts/ensure-mcp-host.sh --check   # exit 0 if healthy
bash scripts/ensure-mcp-host.sh           # repair if needed
# Or via CLI (same scripts under the hood):
orchestrator ensure --check               # MCP + host tools (rg)
orchestrator ensure --mcp                 # MCP only (repair if needed)
orchestrator ensure --host-tools --yes    # ripgrep non-interactive
# Grok: enable orchestrator-host in .grok/config.toml (template default: enabled)
```

Needs **uv** (preferred when `ensurepip` is missing) or `sudo apt-get install -y python3-venv`.

### Host CLI self-upgrade (package on PATH)

When `orchestrator version` lags the template (e.g. uv tool still on 1.9.0 after a 1.9.5 release):

```bash
orchestrator self-upgrade                 # dry-run plan (default)
orchestrator self-upgrade --to 1.9.5 --yes
orchestrator self-upgrade --from-github --yes   # target GitHub latest
# channel: auto | uv_tool | pip
orchestrator self-upgrade --method uv_tool --yes
```

This upgrades the **host package only** — not an app tree. For apps use `orchestrator upgrade /path/to/app`.

### In-app install that survives branch switches

Git stores files per commit. After `init`/`upgrade` on one branch, other branches will **not** have skills/scripts unless you make the install **project-global**:

```bash
cd /path/to/your-app
# Current branch must already have .orchestrator-version (from init/upgrade)
orchestrator install-persist .
# optional multi-machine:
git push -u origin orchestrator/installed
```

What that does:

1. Branch **`orchestrator/installed`** → pointer at the install commit (baseline)
2. **`.githooks/post-checkout`** + `core.hooksPath=.githooks` → on every branch switch, restore surfaces from the baseline
3. **Broadcast** orchestrator paths onto **all local** branches (one-time)

Uses `scripts/orchestrator-branch-sync.py` (**stdlib only** — no pip package required in the app).

| Symptom | Fix |
|---------|-----|
| Switch branch → no `.grok` / no lock | `orchestrator install-persist .` on a branch that still has the install |
| Hook silent no-op | Ensure `scripts/orchestrator-branch-sync.py` is deployed (scripts selection) and `git config core.hooksPath` is `.githooks` |
| Other machine still missing | Push `orchestrator/installed` and pull; run `install-persist` once per clone |

**Default (safe):** upgrade only touches the **current branch**. No multi-branch commits.

| Env | Effect |
|-----|--------|
| *(none)* | Current branch only |
| `ORCHESTRATOR_BRANCH_BROADCAST=1` | **Dangerous** — commit orchestrator paths onto **every** local branch |
| `ORCHESTRATOR_INSTALL_BRANCH_HOOK=1` | Install post-checkout auto-sync hook |
| `ORCHESTRATOR_NO_BRANCH_SYNC=1` | Full suppress (legacy kill-switch) |

Do **not** enable broadcast on large app repos (many local branches).

---

## Steps — Windows (PowerShell)

### 1. Clone the template

```powershell
git clone https://github.com/ndestates/orchestrator.git
cd orchestrator
```

### 2. Allow script execution for this session (if required)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 3. Run the Windows installer

```powershell
.\scripts\install.ps1
```

Optional CLI package and host tools:

```powershell
.\scripts\install.ps1 -Cli
# equivalent:
python -m pip install -e .

# or npm wrapper (Node 18+):
.\scripts\install.ps1 -Npm

# ripgrep for CSE (or use WSL and install-host-tools.sh):
.\scripts\install.ps1 -HostTools
# equivalent:
.\scripts\install-host-tools.ps1 -Yes

# equivalent:
npm install -g .

# optional local Ollama on the host (BYOM):
.\scripts\install.ps1 -Ollama
# or: .\scripts\install-ollama.ps1
# see docs/guides/local-ollama.md
```

### 4. Verify CLI

```powershell
orchestrator version
# or:
python -m orchestrator_cli version
```

### 5. Install into one application repo

```powershell
orchestrator init C:\path\to\your-app --no-pr --dry-run
orchestrator init C:\path\to\your-app --no-pr
orchestrator status C:\path\to\your-app --json
```

---

## Package install (npm)

Node.js 18+. Package name: `@ndestates/orchestrator`. The npm bin is a thin shim (`bin/orchestrator.js`) that always runs `python -m orchestrator_cli` (never recurses into the npm shim).

```bash
# from this repo
npm install -g .

# when published
npm install -g @ndestates/orchestrator
```

`scripts/npm/postinstall.js` installs the Python package (`pip install -e .` from a git checkout, or `pip install orchestrator==VERSION` from a published tarball).

## Package install (pip / wheel)

**Production (GitHub Release wheel — preferred):**

```bash
VER=2.2.0
uv tool install --force \
  "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
# or:
pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
```

From a checkout of this repository:

```bash
python3 -m pip install -e .
# or: bash scripts/install.sh --uv-tool
```

The project package name is `orchestrator` (see root `pyproject.toml`). Version is read from the root `VERSION` file (semver). The wheel can bundle deployable template surfaces for offline init when built with Hatch.

PyPI-style (when published):

```bash
python3 -m pip install orchestrator==2.2.0
```

Use a virtual environment recommended for isolation. See [Production ship](../guides/production-ship.md).

---

## What the bootstrap installers do

| Action | `install.sh` | `install.ps1` |
|--------|--------------|---------------|
| Require git + Python | Yes | Yes |
| Create `.github/agents`, prompts, `docs/codebase`, `TODO` | Yes | Yes |
| Run `scripts/sync_manifests.py` | Yes | Yes |
| Validate manifests + cache README | Yes | Yes |
| Optional `pip install -e .` | `--cli` | `-Cli` |
| Operator profile scaffold | `setup-who-i-am.sh` | Manual (see who-i-am setup) |

They **do not** push template files into other apps. That is `orchestrator init` / `upgrade` only.

## What `orchestrator init` / `upgrade` do

Clean-deploy flow (high level):

1. License gate (only if `ORCHESTRATOR_LICENSE_URL` is set — see [Licensing](../reference/licensing.md))
2. Create a feature branch on the target
3. Materialize selected template surfaces (from `scripts/deploy-bundle.yaml`)
4. Customize / decontaminate for the project slug
5. Write lock file, commit, optional PR

Flags you will use often:

| Flag | Purpose |
|------|---------|
| `--dry-run` | Plan only; no writes |
| `--no-pr` | Commit without opening a PR |
| `--selections` | Comma list or bundle defaults (e.g. `grok,chains`) |
| `--profile` | Stack profile name when applicable |
| `--to` / `--version` | Target template version for upgrade |

## Upgrade your apps after a release

**Runbook:** [Per-app upgrade](../guides/per-app-upgrade.md) (no fleet wave).

```bash
# from orchestrator at the release tag
orchestrator upgrade /path/to/your-app --no-pr --dry-run
orchestrator upgrade /path/to/your-app --no-pr
```

## Fleet wave (removed)

Multi-app fleet scripts and `orchestrator wave` are **deleted**. There is no env override.
Historical notes: [Wave deploy log](../guides/wave-deploy-log.md).

## After install

1. Edit `.grok/memories/who-i-am.md` if present ([Who I am setup](who-i-am-setup.md))
2. Start a session: `/chain session-start`
3. Read [Quickstart](quickstart.md) for the first day workflow

## Verify

| Check | Expected |
|-------|----------|
| `bash scripts/install.sh` or `.\scripts\install.ps1` | Completes without ERROR |
| `orchestrator version` | Prints CLI + template version |
| `orchestrator license` | Disabled (local) or valid lease |
| `orchestrator status /path/to/app` | Lock / drift JSON when installed |
| `orchestrator wave` | Unknown command (removed) |

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Missing required file | Restore from git history; re-run bootstrap |
| `orchestrator` not found | Use `python -m orchestrator_cli …` or ensure pip Scripts/bin on PATH |
| Working tree not clean | Commit or stash on the **target app** before init/upgrade |
| License check failed | See [Licensing](../reference/licensing.md); unset URL for local-only |
| Wave script BLOCKED | Intended — use per-app upgrade |

## Next steps

- [Licensing](../reference/licensing.md)
- [Quickstart](quickstart.md)
- [Template deploy (per-app)](../guides/template-deploy.md)

## Related

- Root [INSTALL.md](../../INSTALL.md)
- [Template adoption](../TEMPLATE_ADOPTION.md)
- CLI package: `src/orchestrator_cli/` (in-repo; entry `orchestrator` via `pyproject.toml`)
