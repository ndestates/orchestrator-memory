# Cache and token savings

[UPDATED 2026-07-18] — link context-window literacy

## Overview

This template is **manifest-first and cache-first** so agents load a small, durable spine instead of re-scanning the whole repo every turn. That cuts **context tokens**, **turn cost**, and **time-to-useful answer**.

This page is for humans: operators and adopters who want to see **what** is loaded, **why** it is capped, and **how much** smaller a lean session is than a naive full load. It is not Docusaurus — plain Markdown under `docs/`, same as the rest of the hub.

**Start here for literacy (why context is scarce):** [Context-window literacy](context-window-literacy.md).

**Policy source of truth:** `token_policy` and `chain_policy` in the project manifest (see [Manifest](../reference/manifest.md)).

## Before you begin

- You have run [Quickstart](../getting-started/quickstart.md) or `/chain session-start` at least once.
- You can open `.grok/project-manifest.yaml` (or the synced copy under `.claude/` / `.github/`).
- Optional: token meter skill available (`/token-usage-meter`) so you can measure your own sessions.

## 1. What “cache” means here

| Layer | Path | Role |
|-------|------|------|
| **Agent cache** | `docs/codebase/*` | Stable map of stack, architecture, concerns — written by `/read-codebase` / documentation chains |
| **Spine** | Manifest + index + TODO + freshness | Always allowed in lean mode (does **not** count toward the extra-file cap) |
| **Capped extras** | Up to `max_cache_files_default` topic docs | Default **2** extra `docs/codebase/*.md` (or memories) after the spine |
| **Vault** | `reports/vault/events.jsonl` | Durable lessons between days — brief at session-start, not a full dump |
| **MCP tools** | `mcp-server/` | Section-sized reads (`get_project_manifest`, `read_cache_file`, `get_chain_detail`, …) instead of whole files |

**Cache is not** “hide everything from the model.” It is “load the **right small set** first, then expand only when the task needs it.”

## 2. Lean vs standard vs deep (policy)

From default `token_policy` in this template:

| Mode | Intent | Typical load |
|------|--------|----------------|
| **`lean` (default)** | Daily feature work | Spine + ≤2 extra cache docs; grep headings before section reads; no app source until you confirm direction |
| **`standard`** | Broader design / multi-file review | Same spine; prompts may allow more cache files |
| **`deep`** | Full map / major refresh | May include `/read-codebase` and larger scans — **expensive**; use deliberately |

Hard rules that save the most tokens in **lean**:

| Rule | Why it saves |
|------|----------------|
| `max_cache_files_default: 2` | Stops “load every docs/codebase file every session” |
| `grep_before_read: true` | One heading match + section read ≪ whole file |
| `no_source_until_confirmed: true` | Avoids silent walks of `app/`, `src/`, etc. |
| `shared_cache_across_steps: true` | One cache load for a whole `/chain` — no re-read at every skill |
| `max_handoff_tokens: 80` | Chain steps pass short handoffs, not full transcripts |
| `session_refresh_context_tokens: 100000` | Soft stop: open a fresh session when context is bloated |

## 3. Worked size comparison (this repo)

Numbers below are **order-of-magnitude proxies** from file sizes in the orchestrator template (measured **2026-07-11**). Token estimates use **≈ chars ÷ 4** (rough; real BPE/tokenizers differ). Use them to compare **relative** cost, not for billing.

### A. Lean session spine (preferred)

| Artifact | ~Lines | ~Chars | ~Tokens (÷4) |
|----------|--------|--------|--------------|
| `docs/codebase/.codebase-freshness.txt` | ~20 | ~0.9k | ~0.2k |
| `docs/codebase/SECTIONS.md` (index; grep then one section) | ~108 total | ~2.9k full | ~0.1–0.7k if section-only |
| `docs/codebase/README.md` (first ~80 lines / headings) | ~80 | ~6k full | ~0.4–1.6k bounded |
| Latest `TODO/*.md` (open items only) | varies | small | typically **≪ 1k** if grepped |
| Manifest `token_policy` slice | small | small | **≪ 1k** |

**Ballpark lean spine:** on the order of **a few thousand** tokens of project cache — not tens of thousands — before any task-specific work.

### B. Naive / expensive loads (avoid in lean)

| Artifact | ~Lines | ~Chars | ~Tokens (÷4) | Note |
|----------|--------|--------|--------------|------|
| `docs/codebase/.codebase-scan.txt` | ~570 | ~20k | **~5k** | Full scan dump — **forbidden** in lean / session-start |
| Full `chains/registry.yaml` | ~2.8k | ~75k | **~19k** | Grep `id:` / use MCP `get_chain_detail` instead |
| All `docs/codebase/*.md` at once | hundreds | tens of k | **many k** | Cap is **2** extras after spine |
| Unscoped `Glob **/*` + multi-file source reads | unbounded | unbounded | **session-killing** | Wait for user confirmation |

### C. Relative savings (illustrative)

Compare three session-open strategies on **this** tree:

| Strategy | What gets loaded | Relative cost |
|----------|------------------|---------------|
| **Lean + MCP/section** | Freshness + index section + TODO open items + at most 2 topic docs | **Baseline (1×)** |
| **Lean + one mistake** | Baseline **plus** full `.codebase-scan.txt` | **~+5k tokens** on open alone |
| **Naive** | Full registry + full scan + every codebase doc | **~5–10×+** of baseline before you type a feature request |

**Takeaway:** a single full read of `chains/registry.yaml` can cost as much as **several lean spines**. Grep or MCP for one chain block instead.

### D. MCP vs full-file Read

| Need | Prefer | Avoid |
|------|--------|--------|
| Manifest / `token_policy` | MCP `get_project_manifest` (or small YAML slice) | Pasting entire manifest every turn |
| One cache section | MCP `read_cache_file` / grep + `offset`/`limit` | Full `ARCHITECTURE.md` when you need one heading |
| One chain | MCP `get_chain_detail` or registry grep by `id:` | Full `chains/registry.yaml` |
| Latest TODO | MCP `get_latest_todo` | Reading every file under `TODO/` |

MCP is **dev-only** (`mcp-server/`); host vs DDEV wiring is in [MCP README](../../mcp-server/README.md) and [multi-platform tool use](../reference/tools/multi-platform-tool-use.md). When MCP is off, the **same discipline** applies with grep + section reads.

## 4. How chains multiply savings

Without shared cache:

```text
skill A loads cache → skill B loads cache again → skill C loads cache again
```

With `shared_cache_across_steps: true` (default):

```text
/chain session-start
  load cache once → standup → meter → lean mode
  handoffs ≤ ~80 tokens each
```

Also:

- **session-end** (mid-day) writes a small pause checkpoint — does **not** require re-scanning the repo to leave.
- **eod-shutdown** closes the day once; vault gets a compact lesson, not a transcript dump.
- **loop-compound** promotes short lessons into vault/STATE — next session-start reuses them via brief, not full history.

## 5. Measure savings in your sessions

### Token meter (recommended)

```text
/token-usage-meter
```

Or:

```bash
python3 .grok/skills/token-usage-meter/scripts/token_monitor.py --sync --project .
```

Artifacts:

| Path | Use |
|------|-----|
| `reports/tokens/latest-summary.json` | Latest context size, turn delta, estimated cost |
| `reports/tokens/session-log.jsonl` | Trend across turns |

**How to read it**

| Signal | Healthy lean pattern | Investigate |
|--------|----------------------|-------------|
| Context after session-start | Rises once, then grows slowly with work | Jump of **≥15k** in one turn without a large intentional paste |
| Status WARNING / CRITICAL | Occasional on big reviews | Every turn after “small” questions |
| Context approaching **100k** | Plan `/chain session-start` in a **new** chat | Keep stacking full-file reads |

Example shape from a real meter file (values change per session):

```json
{
  "context_tokens": 34515,
  "turn_delta": 34515,
  "status": "warning",
  "warnings": ["Last turn added +34,515 tokens (≥15,000). Review large reads or verbose output."]
}
```

A **warning** is a prompt to ask: *did we load the full registry, scan dump, or broad source?* — not always a failure.

### Lightweight file-size audit (no API)

Compare proxies anytime (committed example script):

```bash
python3 docs/examples/cache-load-size-audit.py
```

Re-run after a cache rebuild if sizes drift; update mental models, not billing claims.

## 6. Operator checklist (keep savings real)

1. Start with `/chain session-start` — do not improvise a full-repo brief every morning.
2. Cite which cache files you used (agents must; humans should too when reviewing).
3. Prefer **one** extra topic doc (`CONCERNS`, `ARCHITECTURE`, …) until blocked.
4. Never `Read` `.codebase-scan.txt` in lean mode — use `.codebase-freshness.txt` or `cache_freshness_check.py`.
5. For chains: grep `id:` or MCP detail — do not paste the whole registry.
6. At **~100k** context, start a new session rather than “one more full scan.”
7. Mid-day leave: `/chain session-end`. End of day: `/chain eod-shutdown`.

## 7. Example: same question, two costs

**Question:** “What does session-end do?”

| Approach | Actions | Cost profile |
|----------|---------|--------------|
| **Lean** | Grep `id: session-end` in `chains/registry.yaml` (or MCP `get_chain_detail`) → read ~40 lines of that block | Small, targeted |
| **Naive** | Read entire `chains/registry.yaml` + all of `docs/codebase/` + full scan file | **~20k+ tokens** before answering |

Same answer quality for this question; the lean path is the product intent.

## Verify

- [ ] You can explain spine vs `max_cache_files_default` without opening source trees.
- [ ] You know full `chains/registry.yaml` and `.codebase-scan.txt` are **anti-patterns** in lean.
- [ ] You can run the token meter or the file-size script above.
- [ ] Hub link from [Guides index](index.md) reaches this page (≤2 clicks from [docs hub](../index.md)).

## Next steps

- [Daily workflow](daily-workflow.md) — session-start / session-end / eod
- [Chains and skills](chains-and-skills.md) — shared cache + short handoffs
- [Manifest reference](../reference/manifest.md) — every `token_policy` field
- [MCP multi-platform tools](../reference/tools/multi-platform-tool-use.md) — section tools
- [Knowledge vault](knowledge-vault.md) — durable lessons without transcript dumps

## Related

- Agent skill (enforced in sessions): `.grok/skills/cache-efficient/SKILL.md`
- Token meter skill: `.grok/skills/token-usage-meter/SKILL.md`
- MCP server: [mcp-server/README.md](../../mcp-server/README.md)
- Architecture cache: [docs/codebase/ARCHITECTURE.md](../codebase/ARCHITECTURE.md)
