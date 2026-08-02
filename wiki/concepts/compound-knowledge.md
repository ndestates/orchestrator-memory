---
title: Compound knowledge
updated: 2026-07-15
sources:
  - sources/karpathy-llm-wiki.md
  - sources/knowledge-vault.md
---

# Compound knowledge

**Definition:** Knowledge that is written once into a durable artifact and **updated** when new sources arrive, so later queries reuse synthesis instead of re-assembling fragments.

## Orchestrator mapping

| Mechanism | Compounds what |
|-----------|----------------|
| `docs/codebase/` | Code orientation (batch refresh / dense maps) |
| `wiki/` | Multi-source judgment, research, decisions |
| `reports/vault/` | Scrubbed lessons + provenance graph |

## Rule

Create wiki pages only when they **compress** ≥2 sources or non-greppable narrative (`wiki_policy.compress_or_skip`).
