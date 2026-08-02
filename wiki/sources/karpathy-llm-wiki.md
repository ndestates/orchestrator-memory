---
title: Karpathy LLM Wiki (source summary)
source: raw/research/2026-07-15-karpathy-llm-wiki.md
ingested: 2026-07-15
tags: [pattern, knowledge, karpathy]
---

# Karpathy LLM Wiki

## One-line

Compile knowledge into an LLM-maintained markdown wiki; do not re-derive from raw documents on every question.

## Takeaways

1. **Raw** is immutable; **wiki** is LLM-owned; **schema** disciplines ops.
2. Ops: **ingest**, **query** (file answers back), **lint**.
3. **index.md** + **log.md** navigate growth without embeddings at small scale.
4. Humans curate sources and questions; LLM does bookkeeping.

## Links

- Concept: [compound-knowledge](../concepts/compound-knowledge.md)
- Concept: [three-layer-architecture](../concepts/three-layer-architecture.md)
- Entity: [orchestrator-knowledge-surfaces](../entities/orchestrator-knowledge-surfaces.md)
- Plan: `reports/research/llm-wiki-karpathy-plan.md`
