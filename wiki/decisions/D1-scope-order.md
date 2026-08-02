---
title: D1 — Wiki scope order
decided: 2026-07-15
status: accepted
reversal: If pilot shows code teams need wiki more than template meta, allow app-first mode via wiki_policy without changing compress-or-skip.
---

# Decision D1 — Scope order

## Decision

1. Template **meta-knowledge** first (this pilot).
2. Per-app wiki is **opt-in** (`deploy_selection: wiki`, `wiki_policy.mode`).
3. Application **code facts** stay in `docs/codebase/`.

## Rationale

Matches Phase 0 lock; reduces blast radius; aligns with code-wiki economics (dense maps beat entity sprawl).

## Links

- Plan: `reports/research/llm-wiki-karpathy-plan.md` §4 D1–D2
