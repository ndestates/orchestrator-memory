# Orchestrator MCP Server

Enterprise-grade [Model Context Protocol](https://modelcontextprotocol.io) server for the orchestrator template and forked app repos.

## Roles — you are not missing a client

**The AI host is the MCP client.** Orchestrator ships only the **server** (this package). Grok, Claude Code, Cursor, Copilot, Gemini, and ChatGPT/Codex load client config and spawn the server process.

```text
┌──────────────────────────────┐     MCP stdio / HTTP      ┌─────────────────────────────┐
│  AI host (MCP CLIENT)        │  list_tools / call_tool   │  orchestrator-mcp (SERVER)  │
│  Grok · Claude · Cursor · …  │ ────────────────────────► │  mcp-server/                │
│  .grok/config.toml, etc.     │ ◄──────────────────────── │  sandboxed cache tools      │
└──────────────────────────────┘                           └─────────────────────────────┘
         │ native Read/Bash fallback when MCP down
         ▼
   skills · chains · session-start scripts
```

| Piece | Role |
|-------|------|
| **This package** | **Server** — cache-first tools for agents |
| **Host config** (`.grok/config.toml`, `.cursor/mcp.json`, …) | **Client wiring** — how the host starts the server |
| **`scripts/mcp-host-stdio.sh`** | Launcher the host executes |
| **`scripts/mcp-smoke.sh`** | Operator/CI smoke: `list_tools` + `health_check` (no IDE) |

There is **no** first-party “Orchestrator MCP client product.” That would duplicate the host. Session-start and chains still work when MCP is `pending`/`fail` via scripts and file tools.

**Tool selection:** the host discovers tools; the **model** chooses from tool descriptions + skill/chain instructions (prefer MCP over huge YAML reads). Optional design for a future `recommend_tools` helper: `docs/internal/MCP-RECOMMEND-TOOLS-SCHEMA.md`.

## Features

- **Manifest-first** — reads `.github/project-manifest.yaml` (or `.claude/` copy)
- **Cache-first tools** — bounded reads of `docs/codebase/*`, TODO, STATE, chains registry
- **Auth** — API key for HTTP; stdio local mode (no key required)
- **Audit log** — append-only JSONL under `reports/mcp/`
- **Path sandbox** — all reads confined to `PROJECT_ROOT`
- **Read-only audits** — allowlisted `chain-audit.sh`, `loop-audit.sh`, `check_name_alignment.py`

## Develop only (never public hosts)

**MCP is a developer-machine tool.** Do not run it on DigitalOcean App Platform, public Kubernetes, Heroku, or any publicly hosted environment. Session-start (`detect-project-runtime.sh`) sets `mcp_policy=dev_only` and blocks when public/prod env markers are present (`mcp_ready=blocked`).

When MCP is not ready, agents must **offer** start options (do not auto-start without choice):

| Option | When | How |
|--------|------|-----|
| **DDEV** | App repos with `.ddev/` | `ddev start` + `Dockerfile.mcp` + enable `orchestrator-ddev` |
| **Docker Compose + host stdio** | Compose apps | App via compose; MCP via `scripts/mcp-host-stdio.sh` on the operator machine |
| **Local host stdio** | Orchestrator template / no DDEV | `bash scripts/ensure-mcp-host.sh` (uv or python3-venv); enable host MCP in the client |

### Client configs (all platforms)

| Host | Config |
|------|--------|
| **Grok** | `.grok/config.toml` (`orchestrator-host` / `orchestrator-ddev`) |
| **Cursor** | `.cursor/mcp.json` · `mcp-server/config/mcp.cursor*.json` |
| **Claude** | `.claude/mcp.claude.example.json` · `mcp-server/config/mcp.claude*.json` |
| **Copilot (VS Code)** | `mcp-server/config/mcp.copilot.vscode*.json` |
| **Gemini** | `.gemini/mcp.gemini.example.json` |
| **ChatGPT / Codex** | `.chatgpt/mcp.chatgpt.example.json` · `mcp-server/config/mcp.chatgpt*.json` |

All host examples launch `scripts/mcp-host-stdio.sh` (ensure + stdio). DDEV examples use `scripts/mcp-ddev-stdio.sh`.

## Manifest identity

`get_project_manifest` includes an `identity` object. When `identity.status` is `template_residue` or `warn`, the manifest still looks like the stock orchestrator **Project Template** — customize `project-manifest.yaml` before trusting stack/runtime. CLI: `python3 scripts/check-project-manifest.py --json`.

## Local DDEV (recommended for app repos)

**Yes — host in DDEV, not DigitalOcean.** Production apps stay on DO; the MCP server is a **dev-only** agent tool and belongs in your local DDEV stack alongside PHP/MySQL.

### Option A — stdio via DDEV (best for Cursor and Grok Build)

No HTTP port, no remote exposure. Cursor or Grok spawns the server inside the web container on demand.

1. Ensure `mcp-server/` is in the project (template deploy or `deploy-mcp-wave.sh`).
2. Add MCP deps to the DDEV web image (once per project):

   ```bash
   mkdir -p .ddev/web-build
   cp mcp-server/ddev/Dockerfile.mcp .ddev/web-build/Dockerfile.mcp
   ddev restart
   ```

3. `ddev start`
4. Enable client config (portable git-root launcher — no absolute paths):
   - **Cursor:** copy `mcp-server/config/mcp.cursor.ddev.example.json` → `.cursor/mcp.json` (or deploy `--selections mcp`)
   - **Grok Build:** copy `mcp-server/config/mcp.grok.project.example.toml` → `.grok/config.toml`, then `/mcps` → enable `orchestrator-ddev`

The wrapper runs:

```text
ddev exec → python3 -m orchestrator_mcp.server --transport stdio
```

with `PROJECT_ROOT=/var/www/html` (same tree as Laravel/artisan).

### Option B — HTTP daemon in DDEV (optional)

For HTTP-based MCP clients, merge `mcp-server/config/ddev.config.snippet.yaml` into `.ddev/config.yaml`, then `ddev restart`.

Reachable at:

- `http://<project>.ddev.site:8090/mcp`
- `https://<project>.ddev.site:8091/mcp`

Set `ORCHESTRATOR_MCP_API_KEY` in `web_environment` if you enable auth.

### Orchestrator template repo (no DDEV)

The template itself has no `.ddev/`. Use host stdio (below) or add a `generic` DDEV project if you prefer container parity.

## Quick start (stdio — host, no DDEV)

```bash
cd /path/to/project
# Preferred: one-shot ensure (uv or python3-venv; used by session-start too)
bash scripts/ensure-mcp-host.sh
# Launcher used by Grok/Cursor (repairs venv, then stdio):
bash scripts/mcp-host-stdio.sh
```

Client config:

- **Grok:** `.grok/config.toml` → `orchestrator-host` with `args = ["scripts/mcp-host-stdio.sh"]` (see `mcp-server/config/mcp.grok.host.example.toml`)
- **Cursor:** `mcp-server/config/mcp.cursor.example.json` → `.cursor/mcp.json` (`cwd` = workspace root)

`detect-project-runtime.sh` / session envelope **auto-repair** the host venv when `mcp-server/` is present so MCP is ready from session-start instead of failing on first connect.

## HTTP on host (not for production)

```bash
export PROJECT_ROOT=/path/to/project
export ORCHESTRATOR_MCP_API_KEY="$(openssl rand -hex 32)"
mcp-server/.venv/bin/orchestrator-mcp --transport streamable-http --host 127.0.0.1 --port 8090
```

Bind to `127.0.0.1` only — do not expose on DO without a proper auth gateway.

## Deploy to app repos

From orchestrator repo:

```bash
bash scripts/deploy-mcp-wave.sh              # dry-run
bash scripts/deploy-mcp-wave.sh --apply      # copy mcp-server + config to wave apps
```

Or bundle selection:

```bash
python3 scripts/deploy_grok_to_project.py /path/to/app --selections mcp
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROJECT_ROOT` | cwd | Repo root (sandbox boundary) |
| `ORCHESTRATOR_MCP_API_KEY` | — | Required for HTTP when set |
| `ORCHESTRATOR_MCP_AUDIT_DIR` | `reports/mcp` | Audit log directory |
| `ORCHESTRATOR_MCP_MAX_READ_BYTES` | `65536` | Max bytes per file read |

## Security

- **Read-only, allowlisted reads** — confined to `PROJECT_ROOT` with a path/prefix allowlist (`sandbox.py`); `.env`, `.git`, and host-app source are denied. Traversal and symlink escapes are rejected after resolution.
- **No arbitrary shell execution** — only the three allowlisted audits (`chain`, `loop`, `alignment`) run, as argv (no shell), cwd=`PROJECT_ROOT`, timeout 120s.
- **HTTP fails closed** — `--transport streamable-http` refuses to start without `ORCHESTRATOR_MCP_API_KEY`; a non-loopback host always requires a key. Unauthenticated HTTP is only possible on a loopback host with the explicit `--allow-insecure-http` flag.
- **Request-time bearer auth** — when a key is set, every HTTP request is verified (constant-time) by a streaming-safe ASGI middleware. If the FastMCP build cannot expose its app, the server refuses to serve HTTP rather than run unauthenticated.
- **stdio is local-only** — unauthenticated by design (stdin/stdout); prints a warning and is bounded by the same read allowlist.
- **Audit log** — append-only JSONL under `reports/mcp/` for every tool call (incl. denied attempts).
- **CI-enforced** — `.github/workflows/mcp-security.yml` runs `pytest mcp-server/tests` (incl. sandbox/auth/gate tests) + `bash scripts/mcp-threat-scan.sh` on every change to `mcp-server/`.
- MCP threat scan: `bash scripts/mcp-threat-scan.sh` (or app `ci_security_checklist.sh`)