# ChatGPT / OpenAI — orchestrator custom instructions

Paste into ChatGPT custom instructions, Codex project instructions, or an Agents system prompt.

## Identity

You are working in an **orchestrator** template or forked app repo.  
**Primary surface:** `.chatgpt/` only. Do not load `.grok/skills` or `.claude/commands` as primary procedures.

## Always first

```bash
python3 scripts/session-context-envelope.py --write
```

Honour the compact CTX: branch, resume card, `ask:`, security, vault, MCP policy (`dev_only`).

## Rules

1. **Manifest-first** — read `.chatgpt/project-manifest.yaml` (synced from `.github/`).
2. **Cache-first** — prefer `docs/codebase/`, `TODO/`, `STATE.md` over deep source greps until the user confirms direction.
3. **MCP develop-only** — use host/DDEV stdio MCP for cache/manifest tools; never recommend MCP on public hosts (DO App Platform, public K8s, etc.).
4. **Script-not-shell** — multi-line logic → `scripts/` or `/tmp/agent-*`; no fragile one-liners.
5. **No new dependencies** without explicit operator approval.
6. **Tests** only against test / `:memory:` databases when the stack uses a DB.

## MCP tools (when connected)

Prefer: `get_project_manifest`, `get_latest_todo`, `read_cache_file`, `get_chain_detail`, `health_check`, `run_readonly_audit`.

Enable: copy `.chatgpt/mcp.chatgpt.example.json` into the client MCP config; run `bash scripts/ensure-mcp-host.sh` once.

## Shared paths OK

`TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`, `wiki/`, `mcp-server/`, `VERSION`.
