# Context-window literacy

[UPDATED 2026-07-18]

## Overview

**Context is the scarce resource.** Every token in the model’s window costs money, time, and attention. Large models also show **lost-in-the-middle** behaviour: material buried mid-context is used worse than material at the start or end.

This guide teaches **how to use context well** in the orchestrator product. It does **not** add a vector database, local transformers runtime, or multi-session SDK. Those are out of scope for this initiative.

**Companion guides:**

| Page | Role |
|------|------|
| [Cache and token savings](cache-and-token-savings.md) | What “cache” means, lean vs deep, MCP vs full files |
| [Session context token budget](../reference/session-context-token-budget.md) | Measured envelope savings (~92% vs naive standup) |
| [LLM Wiki](llm-wiki.md) | Optional lean retrieval of wiki pages (not a vector store) |
| [Knowledge vault](knowledge-vault.md) | Hash-chained lessons between sessions |

**Teaching inspiration (visual only):** Sarah Drasner’s *AI 04 Context Windows* and related AI drawings on [sarah.dev/projects](https://sarah.dev/projects) (transformers, MCP, vectors, context) — pedagogy for operators and agents, not a stack mandate.

## Before you begin

- Run `/chain session-start` (or print `reports/sessions/context-latest.txt`).
- Prefer **Grok → `.grok/`**, Claude → `.claude/`, etc. (platform surface).
- Know: PayPal production go-live is **held**; multi-session SDK work stays in **mailchimp** only.

## 1. Mental model

| Idea | Meaning for us |
|------|----------------|
| **Window size** | Hard cap on how much text the model can see this turn |
| **Attention cost** | Roughly grows badly with length (why “paste the whole repo” fails) |
| **Lost-in-the-middle** | Important facts mid-window get weaker recall — keep spine short and put decisions at the edges |
| **Retrieval vs synthesis** | **Retrieve** a small right slice first; **synthesize** only after that |
| **Tokenizer** | Counts differ by model; we estimate ≈ chars/4 for relative budgets only |

## 2. Product rules that protect the window

From default `token_policy` / `chain_policy` (manifest):

| Rule | Default | Literacy one-liner |
|------|---------|-------------------|
| `mode` | `lean` | Daily work stays spine-sized |
| `max_cache_files_default` | `2` | At most two extra cache docs after spine |
| `grep_before_read` | `true` | Find the section before loading the file |
| `no_source_until_confirmed` | `true` | No app source walks until the human confirms |
| `shared_cache_across_steps` | `true` | One cache load per chain |
| `max_handoff_tokens` | `80` | Handoffs are contracts, not transcripts |
| `session_refresh_context_tokens` | `100000` | Open a **fresh** session when bloated |

**Session spin-up target:** compact CTX envelope ≈ **hundreds** of tokens, not multi-thousand skill dumps. See [token budget](../reference/session-context-token-budget.md).

## 3. Good vs bad patterns

### Do

| Pattern | Why |
|---------|-----|
| Print **CTX envelope** first | Fixed-size identity, branch, open/next, pointers |
| **Resume-first** when card is fresh | Skip re-reading TODO/STATE/VISION |
| MCP `read_cache_file` / section Read | Section-sized, not whole ARCHITECTURE |
| Multi-lane Shape B with **contract outputs** | Parallel work without N full chat histories |
| Vault brief ≤ few lessons | Durable memory without replaying the year |
| Wiki **index/log only** at session-start | Lean `wiki_policy` |
| **WebMCP** page tools (beta) for browser agents | Structured tools beat DOM scrape — fewer brittle tokens *on the page*; not a substitute for lean host context |

### Don’t

| Anti-pattern | Why it hurts |
|--------------|--------------|
| Load every `docs/codebase/*` every morning | Cap exists for a reason |
| Re-run full standup skill body after envelope | Doubles procedure tokens |
| Parallel multi-session agents each with full cache | Multiplies window use (mailchimp SDK stays app-local) |
| “Just embed everything in a vector DB” by default | Ops cost; often worse than SECTIONS + vault + grep |
| Paste CI logs + full diffs + full skills into one turn | Middle of the window becomes landfill |
| Keep one chat past ~100k context | Fresh session is cheaper than more clever packing |

## 4. How this relates to Sarah’s AI drawings

| Drawing (sarah.dev) | Takeaway for orchestrator |
|---------------------|---------------------------|
| **Transformers** | Models attend over tokens you pay for — smaller good context beats larger noise |
| **MCP in practice** | Prefer tool/section access over stuffing files into the prompt (we already ship **host** MCP, dev-only) |
| **WebMCP (demo / beta)** | Page declares tools so browser agents call contracts, not DOM scrape — see [WebMCP beta](webmcp-beta.md); still not multi-session |
| **Vector databases** | Optional **later** for real semantic corpora; **not** a substitute for cache-first |
| **Context windows** | Primary product literacy — this page |

## 5. Operator checklist (daily)

1. `/chain session-start` → trust envelope + resume card when fresh.  
2. Confirm direction before any `app/` / large source read.  
3. One chain, one shared cache load.  
4. Handoffs ≤ ~80 tokens.  
5. If answers degrade or meter warns: **fresh session**, don’t “add more context.”  
6. Measure with `/token-usage-meter` when cost matters.

## 6. Out of scope (explicit abandon / hold)

| Topic | Status |
|-------|--------|
| Multi-session Copilot SDK in the template | **Abandoned** for orchestrator — remains in **mailchimp** only |
| Vector DB as default product surface | **Abandoned** for this initiative (use `/chain vector-db-assess` only if a real app RAG need appears later) |
| PayPal production go-live | **Held** (code may exist; no live plans/secrets push) |
| WebMCP as default / host-MCP replacement | **No** — optional **beta** browser page tools only; see [WebMCP beta](webmcp-beta.md) |

## Verify

- [ ] You can explain lean spine vs deep scan in one sentence.  
- [ ] You know where envelope artifacts live (`reports/sessions/context-latest.*`).  
- [ ] You know the three “don’ts” that burn the most tokens.  

## Related

- [Cache and token savings](cache-and-token-savings.md)  
- [Session context token budget](../reference/session-context-token-budget.md)  
- [Daily workflow](daily-workflow.md)  
- [Manifest](../reference/manifest.md)  
- [When to use loops](when-to-use-loops.md)  
- [WebMCP (beta)](webmcp-beta.md) — browser page tools (not multi-session, not host MCP)  

