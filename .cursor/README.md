# Cursor IDE integration (orchestrator template)

**Platform surface:** you are Cursor — use **`.cursor/`** (manifest, rules, mcp.json). Do not prefer `.grok/` or `.claude/` skill trees. Shared: `TODO/`, `docs/`, `scripts/`. See `docs/reference/platform-surfaces.md`.

**Manifest:** read [`.cursor/project-manifest.yaml`](project-manifest.yaml) for stack, paths, and token/chain/loop policy (synced from `.github/project-manifest.yaml`).

**Session spin-up (all platforms share this):**

```bash
python3 scripts/session-context-envelope.py --write
```

Project rule: [`.cursor/rules/session-context-envelope.mdc`](rules/session-context-envelope.mdc) — print the compact CTX envelope; expand on red only. Token budget: `docs/reference/session-context-token-budget.md`.

**MCP:** [`.cursor/mcp.json`](mcp.json) — orchestrator MCP server for cache-first tools (`get_project_manifest`, `read_cache_file`, chain/skill discovery). **Develop only** — never on public hosts. When MCP is not ready, follow envelope `expand: mcp_start` options (DDEV / Docker / host stdio).

After changing the canonical manifest, run `python3 scripts/sync_manifests.py`.