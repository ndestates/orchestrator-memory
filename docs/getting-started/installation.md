# Installation

[UPDATED 2026-09-17] — **one method: `npm install`** · product **3.0.0** · BYOK

## Bring your own keys (required)

Orchestrator does **not** include model-provider API keys or free cloud model access.

| You need | Examples |
|----------|----------|
| **Your own AI host account** | Claude Code, Grok Build, GitHub Copilot, Cursor, Gemini, ChatGPT |
| **Your own API keys** (when using APIs) | Created in **your** OpenAI / Anthropic / xAI / Google / etc. console |
| **Local option (no cloud key)** | [Ollama BYOM](../guides/local-ollama.md) if you prefer models on your machine |

Do **not** commit keys. Details: [Bring your own keys](../reference/bring-your-own-keys.md).

## End users — npm only

**One install method:** `npm install`. There is no fleet/wave install. uv, pip, `install.sh`, VSIX, and git clone are **not** product install paths.

Requires Node.js 18+ and Python 3.10+.

```bash
npm install -g @ndestates/orchestrator
orchestrator version
orchestrator memory brief --seed
```

Put template files in **one** app (explicit; `npm install` does not rewrite `.grok/`):

```bash
cd /path/to/app
npx orchestrator init . --no-pr
npx orchestrator upgrade . --no-pr
```

Upgrade the host package later:

```bash
npm install -g @ndestates/orchestrator@latest
orchestrator version
```

Python 3.10+ is required. If `python -m orchestrator_cli` is missing, the npm shim prints **one** wheel line for the **same** version as the npm package. Install that wheel from the public GitHub Release — do not mix an npm version with a different wheel. Existing app trees stay until you run `upgrade`.

Package: https://www.npmjs.com/package/@ndestates/orchestrator  
Releases (matching wheels): https://github.com/ndestates/orchestrator-memory/releases

### Uninstall

```bash
orchestrator uninstall --host --no-project --apply --yes
# or:
npm uninstall -g @ndestates/orchestrator
# project files (when you mean it):
npx orchestrator uninstall . --apply --yes
```

### DDEV / Laravel / PHP apps

Install from the **host**, not `ddev exec`. The CLI writes git-tracked files into the app.

```bash
npm install -g @ndestates/orchestrator
npx orchestrator check /path/to/app
npx orchestrator init /path/to/app --no-pr --dry-run     # if not installed
npx orchestrator upgrade /path/to/app --no-pr            # preview
npx orchestrator upgrade /path/to/app --yes --no-pr      # apply
```

Do **not** `npm i -D @ndestates/orchestrator` in these PHP apps. Do **not** run `init`/`upgrade` inside the container.

## After template files exist in an app

These steps assume you already ran `npx orchestrator init` (or equivalent). They are not alternate product installs.

### Host tools (ripgrep)

Session-start runs a Cyber Essentials lean scan. Without **`rg`**, several controls print `(rg not available — skipped)`.

| Environment | How to install `rg` |
|-------------|---------------------|
| **Debian / Ubuntu / WSL2** | `sudo apt-get update && sudo apt-get install -y ripgrep` |
| **Fedora / RHEL** | `sudo dnf install -y ripgrep` |
| **Arch** | `sudo pacman -S ripgrep` |
| **macOS** | `brew install ripgrep` |
| **DDEV web** | `webimage_extra_packages: [ripgrep]` in `.ddev/config.yaml`, then `ddev restart` |

### Per-app upgrade (no fleet)

```bash
npx orchestrator check /path/to/your-app
npx orchestrator upgrade /path/to/your-app --no-pr
npx orchestrator upgrade /path/to/your-app --from-github --yes --no-pr
```

`--from-github` uses **public** GitHub Releases on `ndestates/orchestrator-memory` (override with `ORCHESTRATOR_GITHUB_REPO`). See [Per-app upgrade](../guides/per-app-upgrade.md).

### What `orchestrator init` / `upgrade` do

1. License gate (only if `ORCHESTRATOR_LICENSE_URL` is set — see [Licensing](../reference/licensing.md))
2. Create a feature branch on the target
3. Materialize selected template surfaces
4. Customize / decontaminate for the project slug
5. Write lock file, commit, optional PR

| Flag | Purpose |
|------|---------|
| `--dry-run` | Plan only; no writes |
| `--no-pr` | Commit without opening a PR |
| `--to` / `--version` | Target template version for upgrade |

## Fleet wave (removed)

Multi-app fleet scripts and `orchestrator wave` are **deleted**. There is no env override.

## After install

1. Start a session: `/chain session-start`
2. Read [Quickstart](quickstart.md) for the first-day workflow

## Verify

| Check | Expected |
|-------|----------|
| `orchestrator version` | Prints CLI + template **3.0.0** (or the installed 3.x) |
| `orchestrator wave` | Unknown command (removed) |

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `orchestrator` not found | Re-run `npm install -g @ndestates/orchestrator` and ensure the npm global bin is on `PATH` |
| `python -m orchestrator_cli` missing | Install the **matching** GitHub Release wheel printed by the shim (same version as npm) |
| Wheel URL 404 | npm and GitHub Release are out of sync — use a version that has **both** an npm package and a Release wheel, or wait for maintainers to cut matching 3.x artifacts |
| Working tree not clean | Automatic: upgrade/init stash -u, deploy, restore. Pass `--no-stash` only to refuse. |
| License check failed | See [Licensing](../reference/licensing.md); unset URL for local-only |

## Next steps

- [Licensing](../reference/licensing.md)
- [Quickstart](quickstart.md)
- [Template deploy (per-app)](../guides/template-deploy.md)

## Related

- Root [INSTALL.md](../../INSTALL.md)
- [Public vs private repos](../reference/public-private-repos.md)
- [Production ship](../guides/production-ship.md) — how maintainers cut matching Release + wheel + npm
- CLI package: `src/orchestrator_cli/` (in-repo; entry `orchestrator` via `pyproject.toml`)

---

## Maintainer / private factory

**Not the user path.** End users must not clone the private factory or use uv/pip/`install.sh` as the documented install.

| Repo | Visibility | Role |
|------|------------|------|
| [ndestates/orchestrator-memory](https://github.com/ndestates/orchestrator-memory) | **Public** | Product: npm metadata, install docs, GitHub Release wheels |
| [ndestates/orchestrator](https://github.com/ndestates/orchestrator) | **Private** | Factory: full template, internal branches |

Override the default upgrade/release target only when you mean to:

```bash
export ORCHESTRATOR_GITHUB_REPO=ndestates/orchestrator   # private factory
```

Default (unset) is `ndestates/orchestrator-memory`.

### Clone this public product repo

```bash
git clone https://github.com/ndestates/orchestrator-memory.git
cd orchestrator-memory
```

### Clone the private factory (access required)

```bash
git clone https://github.com/ndestates/orchestrator.git
cd orchestrator
```

### uv / pip / install.sh (maintainer only)

These install the Python CLI from a checkout or from a **published** public Release wheel. They are not the product install story.

```bash
# Matching public wheel (same version as npm / VERSION)
VER=3.0.0
uv tool install --force \
  "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
# or:
python3 -m pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"

# From a public or factory checkout
bash scripts/install.sh --uv-tool    # preferred host CLI from tree
bash scripts/install.sh --cli        # pip editable
bash scripts/install.sh --npm        # npm wrapper from checkout
# Windows: .\scripts\install.ps1 -Cli / -Npm
```

Factory / this checkout only: `npm run install:cli` still runs `pip install -e .` (`--force`).

### Host CLI self-upgrade (package on PATH)

```bash
orchestrator self-upgrade                 # dry-run plan (default)
orchestrator self-upgrade --from-github --yes   # target public GitHub latest wheel
```

This upgrades the **host package only** — not an app tree. For apps use `orchestrator upgrade /path/to/app`.

Ship matching artifacts: [Production ship](../guides/production-ship.md).
