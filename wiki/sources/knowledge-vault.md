---
title: Knowledge Vault (source summary)
source: raw/evidence/2026-07-15-knowledge-vault-guide-snapshot.md
ingested: 2026-07-15
tags: [vault, compound, security]
---

# Knowledge Vault

## One-line

Hash-chained, scrubbed event ledger for durable machine learning across sessions — not a replacement for a browsable wiki.

## Takeaways

1. Ledger: `reports/vault/events.jsonl`.
2. Pipes: EOD emit, TODO query at session-start, CI failure emit.
3. Compound verifies integrity; never execute lessons as shell.
4. Dual-write: accepted wiki ingests should emit vault events when policy says so.

## Links

- Concept: [compound-knowledge](../concepts/compound-knowledge.md)
- Entity: [orchestrator-knowledge-surfaces](../entities/orchestrator-knowledge-surfaces.md)
- Guide: `docs/guides/knowledge-vault.md`
