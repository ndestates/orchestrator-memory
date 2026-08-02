# Session context envelope (ChatGPT / OpenAI)

**THIS SURFACE IS CHATGPT — use `.chatgpt/` only for prompts/instructions.**

| You | Primary |
|-----|---------|
| **ChatGPT / Codex** | **`.chatgpt/`** · `.chatgpt/project-manifest.yaml` · `.chatgpt/prompts/` · `.chatgpt/instructions/` |
| Not primary | `.grok/`, `.claude/`, `.github/skills/`, `.gemini/`, `.cursor/` |

Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`. Map: `docs/reference/platform-surfaces.md`.

**Run first** on every project spin-up / session start:

```bash
python3 scripts/session-context-envelope.py --write
export ORCHESTRATOR_AI_PLATFORM=chatgpt   # optional pin
```

## Rules

- Paste or honour the **compact** CTX block. Do not rewrite it as a long summary.
- Prefer **`.chatgpt/`** procedures; do not load Grok/Claude skill novels as primary.
- **Always surface `ask:` / pickup** so the user can continue last work if they wish.
- Surface the **`ws primary=…`** line when present (multi-workstream registry; max 5 ids). See `.chatgpt/prompts/multi-workstream.md`.
- Warn when `behind_develop>0` or `base:` is set before release/version work.
- If `identity` is `template_residue` or `warn`, say so once and treat stack as untrusted until fixed.
- MCP is **develop-only** — use `bash scripts/ensure-mcp-host.sh` + `.chatgpt/mcp.chatgpt.example.json` on a developer machine only.

Token budget: `docs/reference/session-context-token-budget.md`.
