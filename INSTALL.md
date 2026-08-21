> **BYOK:** Use your own model-provider accounts and API keys.  
> See [Bring your own keys](docs/reference/bring-your-own-keys.md).

# Installation

[UPDATED 2026-08-17] — one method: **npm install**

There is **no** fleet/wave install. There is **no** uv/pip/VSIX product path.

## Install

Node.js 18+ and Python 3.10+.

```bash
npm install -g @ndestates/orchestrator
orchestrator version
```

In one app repo (optional, writes git-tracked template files — does not run on `npm install` itself):

```bash
cd /path/to/app
npm install @ndestates/orchestrator
npx orchestrator init . --no-pr
```

Upgrade that app later:

```bash
npx orchestrator upgrade . --no-pr
```

If `python3` is missing, install Python 3.10+. If `python -m orchestrator_cli` is missing, the CLI prints the one wheel line (no auto-pip).

## Uninstall

```bash
npm uninstall -g @ndestates/orchestrator
# project files:
npx orchestrator uninstall . --apply --yes
```

## After install

```text
orchestrator version
/chain session-start
```

Package: https://www.npmjs.com/package/@ndestates/orchestrator  
Guide: [docs/getting-started/installation.md](docs/getting-started/installation.md)
