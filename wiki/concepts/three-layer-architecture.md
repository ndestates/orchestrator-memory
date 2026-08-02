---
title: Three-layer architecture
updated: 2026-07-15
sources:
  - sources/karpathy-llm-wiki.md
---

# Three-layer architecture (Karpathy + orchestrator)

| Layer | Karpathy | Orchestrator |
|-------|----------|--------------|
| Raw | Immutable sources | `raw/` |
| Compiled knowledge | Wiki markdown | `wiki/` (+ code cache for code) |
| Schema | AGENTS/skill rules | `wiki_policy` + `/llm-wiki` schema |
| (extra) Integrity | — | Vault ledger |

Agents load **schema** (skill + manifest), read **wiki index** first, and only open raw when verifying or ingesting.
