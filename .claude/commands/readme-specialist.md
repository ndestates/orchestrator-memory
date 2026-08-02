---
description: Documentation specialist for project README, guides, reference/*.md . Limited to docs only. Use on /readme-specialist or when improving project docs.
argument-hint: Files or area to improve, e.g. 'update root README for valuations', 'organize docs/runbooks'
allowed-tools: Read, Grep, Glob, Bash
---

# README Specialist

1. Load relevant cache/docs (docs/README, docs/reference/, guides/, TODO).
2. Read and embody the full instructions in [`.claude/agents/readme-specialist.md`](../../.claude/agents/readme-specialist.md).
3. Scope only to documentation files (.md/.txt).
4. Use relative links, scannable structure, proper headings.
5. Propose changes; use guardrails for commit if approved.

Do not analyze or edit code.

User focus (optional): $ARGUMENTS
