---
description: Karpathy-style LLM wiki ops: ingest, query, lint, file-answer. Honors wiki_policy.
argument-hint: ingest <path> | query <q> | lint | status
allowed-tools: Read, Grep, Glob, Bash
---

# LLM Wiki

Follow `.claude/commands/llm-wiki/SKILL.md` and `.claude/commands/llm-wiki/references/wiki-schema.md` exactly.

1. Read `wiki_policy.mode` from the platform manifest — stop if `off`.
2. Cache-first: cite policy + `wiki/index.md`.
3. Run the requested op with compress-or-skip and approval gates.
4. Never edit committed `raw/` sources; never put secrets in wiki.

User focus (optional): $ARGUMENTS
