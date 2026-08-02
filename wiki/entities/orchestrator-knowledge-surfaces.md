---
title: Orchestrator knowledge surfaces
updated: 2026-07-15
sources:
  - sources/karpathy-llm-wiki.md
  - sources/knowledge-vault.md
---

# Orchestrator knowledge surfaces

| Surface | Path | Owner | Use when |
|---------|------|-------|----------|
| Code cache | `docs/codebase/` | `/read-codebase` + agents | Greppable product structure, lean session spine |
| LLM Wiki | `wiki/` | `/llm-wiki` | Research, decisions, multi-source synthesis |
| Vault | `reports/vault/events.jsonl` | compound / EOD / scripts | Integrity, cross-session lessons, precedents |
| TODO / STATE | `TODO/`, `STATE.md` | operators + loops | Daily scope and durable loop spine |

## Anti-pattern

Building a second `STRUCTURE.md` as many entity wiki pages for every source file.
