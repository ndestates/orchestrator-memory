# Platform surfaces — use *your* tool tree

[UPDATED 2026-07-21]

Each AI host has its **own** skills, commands, agents, and manifest copy.  
**Models and agents must load procedures from their platform directory**, not from a sibling host’s tree.

## Map

| You are… | **Use (primary)** | Manifest | Skills / commands / rules | MCP client config |
|----------|-------------------|----------|---------------------------|-------------------|
| **Grok Build** | `.grok/` | `.grok/project-manifest.yaml` | `.grok/skills/`, `.grok/config.toml` | `.grok/config.toml` → `orchestrator-host` / `orchestrator-ddev` |
| **Claude Code** | `.claude/` | `.claude/project-manifest.yaml` | `.claude/commands/`, `.claude/agents/`, `CLAUDE.md` | `.claude/mcp.claude.example.json` → Claude Desktop / Code MCP settings |
| **GitHub Copilot** | `.github/` (+ `.copilot/`) | `.github/project-manifest.yaml` | `.github/skills/`, `.github/prompts/`, `.github/copilot-instructions.md`, `.copilot/skills/` | `mcp-server/config/mcp.copilot.vscode.example.json` → VS Code MCP |
| **Google Gemini** | `.gemini/` | `.gemini/project-manifest.yaml` | `.gemini/prompts/`, `.gemini/instructions/` | `.gemini/mcp.gemini.example.json` |
| **Cursor** | `.cursor/` | `.cursor/project-manifest.yaml` | `.cursor/rules/`, `.cursor/mcp.json` | `.cursor/mcp.json` |
| **ChatGPT / OpenAI** | `.chatgpt/` | `.chatgpt/project-manifest.yaml` | `.chatgpt/prompts/`, `.chatgpt/instructions/` | `.chatgpt/mcp.chatgpt.example.json` (Codex / Agents / ChatGPT MCP clients) |

## Hard rules

1. **Primary surface only** for skill/procedure text: if you are Grok, open `.grok/skills/…`, not `.claude/commands/…`.
2. **Manifest:** prefer your platform’s `project-manifest.yaml` (content is synced; path must match host).
3. **Shared project truth is OK** (every host): `TODO/`, `docs/codebase/`, `docs/reference/`, `scripts/`, `reports/`, `STATE.md`, `VISION.md`, `chains/`, `wiki/`, `mcp-server/`, `VERSION`.
4. **Do not prefer** another host’s tree when an equivalent exists under yours (even if paths look similar after sync).
5. **Session-start** still runs the shared script:  
   `python3 scripts/session-context-envelope.py --write`  
   Then load any *extra* procedure from **your** surface only.  
   Compact CTX may include **`ws primary=…`** (multi-workstream registry).  
   Multi-workstream is **one shared implementation** on every host (slash-first).  
   Canonical: `docs/guides/multi-workstream/IMPLEMENTATION.md` · sync:  
   `python3 scripts/sync-multi-workstream-surfaces.py`
6. Optional: set `ORCHESTRATOR_AI_PLATFORM=grok|claude|copilot|gemini|cursor|chatgpt` so the envelope pins `surface platform=…` explicitly.  
   ChatGPT aliases: `openai`, `codex`, `gpt`.

## MCP (all platforms, develop-only)

| Step | Command / file |
|------|----------------|
| Ensure host venv | `bash scripts/ensure-mcp-host.sh` |
| Host launcher | `scripts/mcp-host-stdio.sh` (auto-repair + stdio) |
| DDEV launcher | `scripts/mcp-ddev-stdio.sh` (+ `Dockerfile.mcp` once) |
| Never | Public hosts (App Platform, public K8s, Heroku, …) |

Per-host examples live under each surface and under `mcp-server/config/`. Details: [multi-platform tool use](tools/multi-platform-tool-use.md), [mcp-server/README.md](../../mcp-server/README.md).

## Why

- Hosts load different file layouts (skills vs commands vs rules vs ChatGPT instructions).
- Sync can lag; following the wrong tree causes “file not found” or stale procedures.
- Token waste: loading both `.grok` and `.claude` duplicates the same intent.

## Engine

- `scripts/_engine/platform_surface.py` — map + detect
- Session envelope prints: `surface platform=… root=… manifest=…`

## Sync (maintainers)

Canonical policy often lives under `.github/` or `.grok/`; after edits:

```bash
python3 scripts/sync_manifests.py
python3 scripts/sync_grok_to_github_claude.py   # when skill sync is required

# Register ALL skills as slash commands on every host (Grok · Claude · Cursor · Copilot · Gemini · ChatGPT)
# Run after adding skills under .grok/skills/ (including app-only drops).
python3 scripts/register-all-slash-commands.py
python3 scripts/register-all-slash-commands.py --check   # exit 1 if gaps
```

**Canonical session slash (all hosts):** `/chain session-start`  
**Catalog:** `docs/reference/slash-commands.md` · `chains/slash-catalog.yaml`

Deploy selections: `chatgpt`, `claude`, `gemini`, `mcp`, `copilot`, `github`, …
