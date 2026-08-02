---
description: Run a named chain. Default session opener: /chain session-start
argument-hint: session-start | eod-shutdown | session-end | delivery | always-on-memory | <id or intent>
allowed-tools: Read, Grep, Glob, Bash
---

# Chain — cache-first skill & prompt composition

**Canonical invoke (Grok command line — type this):**

```text
/chain session-start
```

Other common: `/chain eod-shutdown` · `/chain session-end` · `/chain delivery` · `/chain always-on-memory`

Same slash on **Claude Code** (`/chain session-start`) and Copilot (chain skill). Argument = registry chain `id` from `chains/registry.yaml` / `CHAIN.md`. Do **not** invent alternate slash names for chains.

**Purpose:** One shared cache load, minimal handoffs, optional chains. Full phase rules: [`references/workflow.md`](references/workflow.md).

## MCP-first (prefer over Read tool)

When MCP is enabled (`.grok/config.toml` → `orchestrator-host` or `orchestrator-ddev`):

| Need | MCP tool |
|------|----------|
| Manifest / token_policy | `get_project_manifest` |
| Cache file section | `read_cache_file` |
| Latest TODO | `get_latest_todo` |
| Chain block | `get_chain_detail` (never full `chains/registry.yaml` Read) |
| Skill summary | `get_skill_summary` |

Fall back to `Grep` + section `Read` only when MCP unavailable.

## Quick flow

1. **Phase 0** — manifest + grep chain `id:` in registry (or MCP `get_chain_detail`)
2. **Phase 1** — match / opt-out / confirm (scheduled allowlist skips confirm)
3. **Phase 2** — one cache load: spine + `docs/codebase/SECTIONS.md` for section picks; cap `min(chain.max_cache_files, token_policy.max_cache_files_default + 2)`
4. **Phase 3** — steps; ≤80-token handoffs; no re-load cited cache
5. **Phase 4** — summary + `chain-completion-write.sh`

**Token-aware skips:** If token meter status is WARNING/CRITICAL, stay in `/cache-efficient` and skip optional steps unless user asked.

See [`references/workflow.md`](references/workflow.md) for opt-out menu, Phase 5 registry, auto-match table, anti-patterns.

User focus (optional): $ARGUMENTS
