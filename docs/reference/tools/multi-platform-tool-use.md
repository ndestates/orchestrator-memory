# Multi-Platform Tool Use in the Orchestrator Template

[UPDATED 2026-07-21] — ChatGPT surface + unified host/DDEV MCP launchers.

The orchestrator provides tools primarily via the **MCP Server** (Model Context Protocol) and platform-native function calling.

For vault work (e.g. `vault_synthesis.py`), use read_file + bash via MCP or native tools. See guides/knowledge-vault.md.

## Common Tools (via MCP)

See `mcp-server/src/orchestrator_mcp/server.py` for full list:

- `health_check`
- `get_project_manifest`
- `get_cache_freshness`
- `read_cache_file`
- `get_latest_todo`
- `get_loop_state`
- `list_chains`, `get_chain_detail`
- `list_skills`, `get_skill_summary`
- `run_readonly_audit` (chain, loop, alignment)
- wiki helpers (`wiki_status`, `wiki_search_index`, `wiki_read_page`) when enabled

All read-only, sandboxed to `PROJECT_ROOT`. **Develop-only** — never on public hosts.

**Roles:** the AI host is the MCP **client**; `mcp-server/` is the **server**. There is no separate Orchestrator MCP client app — see `mcp-server/README.md`. Design for optional tool ranking: `docs/internal/MCP-RECOMMEND-TOOLS-SCHEMA.md`.

## One-time host prep (every platform)

```bash
bash scripts/ensure-mcp-host.sh          # builds/repairs mcp-server/.venv (uv preferred)
bash scripts/ensure-mcp-host.sh --check  # exit 0 when healthy
bash scripts/mcp-smoke.sh                # stdio handshake: list_tools + health_check
bash scripts/mcp-smoke.sh --quiet        # session-start / CI one-liner
```

Session-start / `detect-project-runtime.sh` auto-repair the host venv when `mcp-server/` is present, then probe handshake. `mcp_ready=fail` means binary may exist but stdio tools failed — run `mcp-smoke.sh` and reconnect the host.

## Platform-Specific Tool Usage

### Grok Build

| Item | Path |
|------|------|
| Surface | `.grok/` |
| MCP | `.grok/config.toml` → `orchestrator-host` or `orchestrator-ddev` |
| Launcher | `args = ["scripts/mcp-host-stdio.sh"]` |

- Skills declare `allowed-tools:` in YAML frontmatter.
- `/mcps` to enable servers after config change.

### Claude (Code / Desktop)

| Item | Path |
|------|------|
| Surface | `.claude/` (+ root `CLAUDE.md`) |
| MCP example | `.claude/mcp.claude.example.json` · `mcp-server/config/mcp.claude.example.json` |
| DDEV | `mcp-server/config/mcp.claude.ddev.example.json` |

1. Copy host example into Claude Desktop / Claude Code MCP settings (merge `mcpServers`).
2. Workspace cwd = repo root so `scripts/mcp-host-stdio.sh` resolves.
3. Commands under `.claude/commands/`; agents under `.claude/agents/`.

### GitHub Copilot (VS Code)

| Item | Path |
|------|------|
| Surface | `.github/` (+ `.copilot/`) |
| MCP example | `mcp-server/config/mcp.copilot.vscode.example.json` |
| DDEV | `mcp-server/config/mcp.copilot.vscode.ddev.example.json` |

1. VS Code MCP uses a `servers` map (not always `mcpServers`) — examples use the VS Code shape.
2. Place under user/workspace MCP config as documented by current VS Code Copilot MCP support.
3. Behavioural tools still guided by `.github/copilot-instructions.md` when MCP is unavailable.

### Gemini

| Item | Path |
|------|------|
| Surface | `.gemini/` |
| MCP example | `.gemini/mcp.gemini.example.json` |
| DDEV | `.gemini/mcp.gemini.ddev.example.json` |
| Function calling | `.gemini/prompts/gemini-tool-calling-example.md` |

- Prefer MCP when the Gemini client supports it (or Cursor with Gemini model).
- Gems use `instructions/` + knowledge uploads for persistent context.

### Cursor

| Item | Path |
|------|------|
| Surface | `.cursor/` |
| MCP | `.cursor/mcp.json` (deployed; host launcher by default) |
| DDEV example | `mcp-server/config/mcp.cursor.ddev.example.json` |

### ChatGPT / OpenAI (Codex, Agents)

| Item | Path |
|------|------|
| Surface | **`.chatgpt/`** (same pattern as Gemini) |
| Manifest | `.chatgpt/project-manifest.yaml` |
| Instructions | `.chatgpt/instructions/chatgpt-orchestrator-instructions.md` |
| Session prompt | `.chatgpt/prompts/session-context-envelope.md` |
| MCP host | `.chatgpt/mcp.chatgpt.example.json` |
| MCP DDEV | `.chatgpt/mcp.chatgpt.ddev.example.json` |
| Canonical | `mcp-server/config/mcp.chatgpt*.json` |

1. Pin surface: `export ORCHESTRATOR_AI_PLATFORM=chatgpt` (aliases: `openai`, `codex`, `gpt`).
2. Ensure venv: `bash scripts/ensure-mcp-host.sh`.
3. Point ChatGPT / Codex / Agents MCP client at the host or DDEV example JSON (stdio `bash scripts/mcp-host-stdio.sh`).
4. Deploy: `orchestrator upgrade … --selections chatgpt,mcp` (or include in broader selections).

## Enabling Tools (checklist)

1. `mcp-server/` present (template or deploy selection `mcp`).
2. `bash scripts/ensure-mcp-host.sh` (host) **or** DDEV + `Dockerfile.mcp`.
3. Platform-specific MCP client file from the table above.
4. Session: `python3 scripts/session-context-envelope.py --write` → expect `mcp=yes` / `mcp_ready=yes` on local.

## Best Practices

- Use tools for cache reads, state, audits to keep context lean.
- Combine with “ask questions first” and sparring.
- Sandbox and audit all tool use (already in MCP).
- Do not run MCP on production/public hosts (`mcp_policy=dev_only`).

See also: [platform-surfaces.md](../platform-surfaces.md), [mcp-server/README.md](../../../mcp-server/README.md).
