# Multi-platform MCP and host tools (production)

[UPDATED 2026-07-21] — **v1.8.8**

Production operator guide: install **ripgrep**, keep **MCP** healthy from session-start, and configure **every AI host** (Grok, Claude, Copilot, Gemini, Cursor, **ChatGPT**).

## Overview

| Concern | Why it matters in production apps |
|---------|-----------------------------------|
| **ripgrep (`rg`)** | Cyber Essentials lean scan + session-security-sweep; without it controls are skipped |
| **Host MCP** | Manifest/cache/TODO tools for agents; broken venv → failed first tool call |
| **Per-host client config** | Each product loads a different surface (`.grok`, `.claude`, …) and MCP file shape |

**Policy:** MCP is **develop-only** (`mcp_policy=dev_only`). Never run it on DigitalOcean App Platform, public Kubernetes, Heroku, or other public hosts.

## Before you begin

- App or orchestrator git repo on a developer machine (or WSL2)
- Python 3.10+; **uv** recommended when `python3-venv` / `ensurepip` is missing
- Clean working tree before `orchestrator upgrade`

## 1. Host tools (ripgrep)

```bash
# Check
bash scripts/install-host-tools.sh --check

# Install (apt/dnf/brew/…; needs sudo on most Linux/WSL hosts)
bash scripts/install-host-tools.sh --yes
# or via bootstrap:
bash scripts/install.sh --host-tools

# Windows PowerShell
.\scripts\install-host-tools.ps1 -Yes
# WSL (preferred for bash scripts):
wsl -e bash -lc 'sudo apt-get install -y ripgrep'
```

| Environment | Install |
|-------------|---------|
| Debian / Ubuntu / **WSL2** | `sudo apt-get install -y ripgrep` |
| Fedora | `sudo dnf install -y ripgrep` |
| macOS | `brew install ripgrep` |
| **DDEV** web | `webimage_extra_packages: [ripgrep]` then `ddev restart` — snippet: `mcp-server/ddev/webimage-extra-packages.snippet.yaml` |
| Docker | `RUN apt-get install -y --no-install-recommends ripgrep` |
| DDEV Dockerfile layer | `mcp-server/ddev/Dockerfile.tools` → `.ddev/web-build/` |

Full tables: [Installation — host tools](../getting-started/installation.md#host-tools-ripgrep).

## 2. MCP host venv (stdio)

```bash
bash scripts/ensure-mcp-host.sh          # check + repair
bash scripts/ensure-mcp-host.sh --check  # exit 0 if healthy
bash scripts/install.sh --mcp            # same path via bootstrap
```

| Script | Role |
|--------|------|
| `scripts/ensure-mcp-host.sh` | Build/repair `mcp-server/.venv`; verify `import mcp` |
| `scripts/mcp-host-stdio.sh` | Client launcher: ensure then `orchestrator-mcp --transport stdio` |
| `scripts/mcp-ddev-stdio.sh` | DDEV web container stdio (app repos) |
| `detect-project-runtime.sh` | **Auto-repairs** host MCP on session-start when `mcp-server/` exists |

Needs **uv** (preferred) or `sudo apt-get install -y python3-venv`.

## 3. Client configuration by host

| Host | Surface | MCP config |
|------|---------|------------|
| **Grok Build** | `.grok/` | `.grok/config.toml` → `orchestrator-host` / `orchestrator-ddev` |
| **Claude Code / Desktop** | `.claude/` | `.claude/mcp.claude.example.json` → merge into Claude MCP settings |
| **GitHub Copilot (VS Code)** | `.github/` + `.copilot/` | `mcp-server/config/mcp.copilot.vscode.example.json` |
| **Gemini** | `.gemini/` | `.gemini/mcp.gemini.example.json` |
| **Cursor** | `.cursor/` | `.cursor/mcp.json` |
| **ChatGPT / Codex / OpenAI Agents** | **`.chatgpt/`** | `.chatgpt/mcp.chatgpt.example.json` |

Host examples all launch:

```text
bash scripts/mcp-host-stdio.sh
```

(DDEV variants use `scripts/mcp-ddev-stdio.sh` + once: copy `mcp-server/ddev/Dockerfile.mcp` → `.ddev/web-build/`.)

Pin surface for the session envelope:

```bash
export ORCHESTRATOR_AI_PLATFORM=chatgpt   # or grok|claude|copilot|gemini|cursor
python3 scripts/session-context-envelope.py --write
```

Maps and rules: [Platform surfaces](../reference/platform-surfaces.md) · [Multi-platform tool use](../reference/tools/multi-platform-tool-use.md).

## 4. Upgrade apps to this template version

After a GitHub release (prefer **v1.8.9+**; v1.8.8 had a lagging template stamp):

```bash
cd /path/to/your-app
# working tree must be clean
orchestrator check .
orchestrator upgrade . --from-github v1.8.9 --yes --no-pr
# or latest:
orchestrator upgrade . --from-github --yes --no-pr
```

Without a published tag, use a local checkout:

```bash
export ORCHESTRATOR_TEMPLATE_ROOT=/path/to/orchestrator
orchestrator upgrade /path/to/app --to 1.8.9 --no-pr
```

Then on the app:

```bash
bash scripts/ensure-mcp-host.sh --check || bash scripts/ensure-mcp-host.sh
bash scripts/install-host-tools.sh --check || bash scripts/install-host-tools.sh --yes
python3 scripts/session-context-envelope.py --write
# expect mcp_ready=yes (or mcp=yes on CTX) and no CSE "rg not available"
```

Runbook: [Per-app upgrade](per-app-upgrade.md).

## 5. Production checklist (developer workstation)

- [ ] `rg --version` works (host and/or `ddev exec rg --version`)
- [ ] `bash scripts/ensure-mcp-host.sh --check` exits 0
- [ ] AI client MCP enabled for this host’s config file
- [ ] `/chain session-start` (or envelope) shows `mcp=yes@dev_only` / `mcp_ready=yes` when appropriate
- [ ] CSE session sweep no longer prints `(rg not available — skipped)` for controls 1/3
- [ ] App lock / `scripts/orchestrator-template-version` matches intended release after upgrade
- [ ] No MCP on public/production deploy targets

## 6. Deploy selections

```bash
# Include MCP package + multi-platform examples
orchestrator upgrade /path/to/app --selections mcp --no-pr

# ChatGPT surface only
orchestrator upgrade /path/to/app --selections chatgpt --no-pr

# Claude / Gemini / full scripts
orchestrator upgrade /path/to/app --selections claude,gemini,scripts,mcp --no-pr
```

Default selections still include `scripts` (launchers + ensure scripts when present in bundle).

## Related

- [Installation](../getting-started/installation.md)
- [Per-app upgrade](per-app-upgrade.md)
- [Platform surfaces](../reference/platform-surfaces.md)
- [mcp-server/README.md](../../mcp-server/README.md)
- [**WebMCP (beta)**](webmcp-beta.md) — **different layer:** browser page tools via `navigator.modelContext` (not host stdio MCP)
- Releases: <https://github.com/ndestates/orchestrator/releases>
