# .chatgpt/ — ChatGPT / OpenAI (Codex, Agents) surface

**THIS SURFACE IS CHATGPT / OPENAI.** Use **`.chatgpt/`** for instructions, prompts, and MCP client examples — not `.grok/`, `.claude/`, or sibling trees.

| You | Primary |
|-----|---------|
| **ChatGPT / Codex / OpenAI Agents** | **`.chatgpt/`** · `.chatgpt/project-manifest.yaml` · `.chatgpt/prompts/` · `.chatgpt/instructions/` |
| Not primary | `.grok/`, `.claude/`, `.github/skills/`, `.gemini/`, `.cursor/` |

Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `mcp-server/`, `chains/`.  
Map: `docs/reference/platform-surfaces.md`.

## Layout

```
.chatgpt/
├── project-manifest.yaml          # synced from .github (python3 scripts/sync_manifests.py)
├── README.md                      # this file
├── instructions/                  # custom instructions / system prompts
├── prompts/                       # reusable prompts (session-start, etc.)
├── mcp.chatgpt.example.json       # host stdio MCP (ensure-mcp + mcp-host-stdio)
└── mcp.chatgpt.ddev.example.json  # DDEV stdio MCP for app repos
```

## Session start (same as every platform)

```bash
python3 scripts/session-context-envelope.py --write
# optional: pin surface
export ORCHESTRATOR_AI_PLATFORM=chatgpt
```

Print the compact CTX; honour `ask:` / resume card; MCP is **develop-only**.

## MCP (develop-only)

1. Ensure host venv once: `bash scripts/ensure-mcp-host.sh`
2. Copy the example into your ChatGPT / Codex / Agents MCP client config:
   - **Host (template / no DDEV):** `mcp.chatgpt.example.json`
   - **DDEV app:** `mcp.chatgpt.ddev.example.json` (+ `Dockerfile.mcp` in `.ddev/web-build/`)
3. Canonical copies also live under `mcp-server/config/mcp.chatgpt*.json`.

Launcher scripts resolve `PROJECT_ROOT` from their path and auto-repair `mcp-server/.venv` (uv preferred).

## Patterns (aligned with Gemini / Claude)

| Pattern | ChatGPT surface |
|---------|-----------------|
| Manifest-first | `.chatgpt/project-manifest.yaml` |
| Cache-first session | `prompts/session-context-envelope.md` |
| Persistent instructions | `instructions/chatgpt-orchestrator-instructions.md` |
| Tools | MCP host/ddev stdio (same server as Grok/Cursor) |
| Deploy selection | `orchestrator upgrade … --selections chatgpt,mcp` |

## Pin platform for envelope

```bash
export ORCHESTRATOR_AI_PLATFORM=chatgpt
# aliases: openai | codex | gpt
```

Strong env hints: `OPENAI_CHATGPT`, `CHATGPT_CODEX`, `CODEX_HOME` (not bare `OPENAI_API_KEY` alone).
