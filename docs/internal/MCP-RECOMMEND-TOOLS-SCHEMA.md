# Design note: MCP `recommend_tools` schema

[UPDATED 2026-07-23] — design only; **not implemented**.

## Purpose

Help agents **select** orchestrator MCP tools without adding a general outbound MCP client or free-form agent router. A single read-only tool would map an intent string to a small allowlisted set of tool names.

## Non-goals

- No calling third-party MCP servers
- No write tools / shell
- No LLM-in-the-tool (static map or simple keyword scoring only)
- Not a replacement for skill prose or host-native tools

## Proposed tool

```text
recommend_tools(intent: str, max_tools: int = 3) -> RecommendToolsResult
```

### Input

| Field | Type | Rules |
|-------|------|--------|
| `intent` | string | Required; free text, max 500 chars; scrubbed as untrusted |
| `max_tools` | int | Default 3; clamp 1–5 |

### Output (`RecommendToolsResult`)

```json
{
  "intent": "string (echo, truncated)",
  "recommendations": [
    {
      "tool": "get_chain_detail",
      "score": 0.92,
      "reason": "intent matches chain/registry lookup",
      "prefer_over": "Read chains/registry.yaml",
      "fallback": "grep id: chains/registry.yaml"
    }
  ],
  "fallback_when_mcp_down": [
    "python3 scripts/session-context-envelope.py --write",
    "bash scripts/chain-audit.sh"
  ],
  "policy": "dev_only_static_map_v1"
}
```

| Field | Meaning |
|-------|---------|
| `tool` | Must exist on this server’s `list_tools` |
| `score` | 0–1 heuristic (keyword / intent bucket) |
| `reason` | One line for the model (not executed) |
| `prefer_over` | Native/file path this tool replaces |
| `fallback` | Script or command when MCP is fail/pending |

## Intent buckets (v1 static map)

| Bucket keywords (examples) | Tools (order) |
|----------------------------|---------------|
| session, standup, start, envelope | `health_check`, `get_project_manifest`, `get_latest_todo` |
| manifest, stack, identity | `get_project_manifest` |
| cache, freshness, codebase docs | `get_cache_freshness`, `read_cache_file` |
| todo, priorities | `get_latest_todo` |
| loop, STATE | `get_loop_state` |
| chain, registry | `list_chains`, `get_chain_detail` |
| skill, skill list | `list_skills`, `get_skill_summary` |
| audit, chain-audit, loop-audit | `run_readonly_audit` |
| wiki | `wiki_status`, `wiki_search_index`, `wiki_read_page` |

Unknown intent → `health_check` + `get_project_manifest` only, `score` ≤ 0.3, reason “default bootstrap”.

## Security

- Same sandbox as other tools; no path args that escape allowlist
- `intent` treated as untrusted data (AI content guardrails)
- Audit every call to `reports/mcp/`
- Fail closed if map references unknown tool names (CI test)

## Implementation sketch (future)

1. `TOOL_INTENT_MAP` in `orchestrator_mcp/recommend.py` (data, not model)
2. Register `@mcp.tool() def recommend_tools(...)`
3. Unit tests: known intents → expected tool set; unknown → defaults; max_tools clamp
4. Document in `docs/reference/tools/multi-platform-tool-use.md` and skill “MCP-first” tables
5. Optional: generate map from tool docstrings later — still no LLM

## Acceptance criteria (when built)

- [ ] `list_tools` includes `recommend_tools`
- [ ] Smoke client can call it
- [ ] Chain skill table cites preferred MCP tool + fallback for session-start / chain load
- [ ] No new dependencies

## Related

- Server roles: `mcp-server/README.md`
- Smoke: `scripts/mcp-smoke.sh`
- Session policy: `scripts/_engine/mcp_runtime_policy.py`
