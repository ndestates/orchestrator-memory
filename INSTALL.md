> **Public product installs:** https://github.com/ndestates/orchestrator-memory/releases  
> **BYOK:** You must use **your own** model-provider accounts and API keys — we do not supply them.  
> See [Bring your own keys](docs/reference/bring-your-own-keys.md).

# Installation Guide

[UPDATED 2026-08-02] — Apache-2.0 freeware · production host packages · BYOK

This repository is a project-agnostic orchestrator template. **Canonical install and licensing docs** live on the documentation site:

| Doc | Contents |
|-----|----------|
| **[Installation](docs/getting-started/installation.md)** | Linux/macOS bash, Windows PowerShell, **npm**, pip, per-app CLI |
| **[Bring your own keys](docs/reference/bring-your-own-keys.md)** | **Required:** your own Claude/Grok/Copilot/Cursor/Gemini/OpenAI accounts & keys |
| **[Production ship](docs/guides/production-ship.md)** | **Ship npm / PyPI / GitHub wheel / VS Code VSIX** — maintainer + user paths |
| **[Host-first memory](docs/guides/host-first-memory.md)** | `orchestrator memory` on any project |
| **[Licensing](docs/reference/licensing.md)** | **Apache-2.0** free; optional self-hosted license server |
| **[Template adoption](docs/TEMPLATE_ADOPTION.md)** | Adopting the template in your product repo |
| **[Template deploy](docs/guides/template-deploy.md)** | Per-app init/upgrade (fleet wave is not the default) |

## Quick start

### Linux / macOS

```bash
bash scripts/install.sh              # bootstrap this repo
bash scripts/install.sh --cli        # also install the Python orchestrator CLI
bash scripts/install.sh --npm        # also install npm wrapper (@ndestates/orchestrator)
bash scripts/install.sh --cli --npm  # both
```

### Windows (PowerShell)

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -Cli
.\scripts\install.ps1 -Cli -Npm
```

### npm (cross-platform)

Node.js 18+. The package is a thin wrapper: postinstall installs the Python CLI; `bin/orchestrator.js` delegates to `python -m orchestrator_cli`.

```bash
# from a git checkout of this repo
npm install -g .

# when published to a registry
npm install -g @ndestates/orchestrator
```

### pip

```bash
python3 -m pip install -e .    # from git checkout
# release wheel (when published):
# python3 -m pip install orchestrator==X.Y.Z
```

### Per-app install (one repository at a time)

```bash
orchestrator init /path/to/app --no-pr --dry-run
orchestrator init /path/to/app --no-pr
orchestrator upgrade /path/to/app --no-pr
```

**Do not** use multi-app wave scripts for routine installs. Fleet deploy requires explicit `ORCHESTRATOR_WAVE_DEPLOY_APPROVED=1` and is deprecated in favour of per-app install.

### Uninstall

**Host CLI** (npm / pip on this machine):

```bash
# preview
bash scripts/uninstall.sh --host
# or: orchestrator uninstall --host --no-project

# apply
bash scripts/uninstall.sh --host --apply
# Windows: .\scripts\uninstall.ps1 -HostPackages -Apply
```

**Project** (remove template surfaces from an app; keeps app source, `registry.app.yaml`, who-i-am):

```bash
orchestrator uninstall /path/to/app              # dry-run
orchestrator uninstall /path/to/app --apply --yes
# optional: --remove-cache --remove-todo --remove-manifests
```

## Requirements

- Git
- Python 3.10+
- Bash 4+ (Linux/macOS bootstrap) or PowerShell 5.1+ (Windows bootstrap)
- Node.js 18+ (optional — only for the npm install path)

## After install

```text
orchestrator version
/chain session-start
```

See [Quickstart](docs/getting-started/quickstart.md) and [Who I am setup](docs/getting-started/who-i-am-setup.md).

## Troubleshooting

See the **Troubleshooting** section in [Installation](docs/getting-started/installation.md).
