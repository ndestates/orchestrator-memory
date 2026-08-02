# Session context envelope (Gemini)

**THIS SURFACE IS GEMINI — use `.gemini/` only for prompts/instructions.**

| You | Primary |
|-----|---------|
| **Gemini** | **`.gemini/`** · `.gemini/project-manifest.yaml` · `.gemini/prompts/` · `.gemini/instructions/` |
| Not primary | `.grok/`, `.claude/`, `.github/skills/`, `.copilot/`, `.cursor/` |

Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`. Map: `docs/reference/platform-surfaces.md`.

**Run first** on every project spin-up / session start:

```bash
python3 scripts/session-context-envelope.py --write
```

## Rules

- Paste or honour the **compact** CTX block. Do not rewrite it as a long summary.
- Prefer **`.gemini/`** procedures; do not load Grok/Claude skill novels as primary.
- **Always surface `ask:` / pickup** so the user can continue last work if they wish. Never auto-checkout.
- Warn when `behind_develop>0` or `base:` is set before release/version work.
- If `identity` is `template_residue` or `warn`, say so once and treat stack as untrusted until fixed.
- MCP is **develop-only** — never recommend running MCP on public hosts.

Optional: cache `reports/sessions/context-latest.txt` (see `gemini-context-caching.md`).

Surface the **`ws primary=…`** line when present (multi-workstream registry). See `.gemini/prompts/multi-workstream.md`.

Token budget: `docs/reference/session-context-token-budget.md`.
