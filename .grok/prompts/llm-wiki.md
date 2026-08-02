---
description: "Karpathy-style LLM wiki ops: ingest, query, lint, file-answer. Honors wiki_policy."
name: "LLM Wiki"
argument-hint: "ingest <path> | query <q> | lint | status"
---

# LLM Wiki

Follow `.grok/skills/llm-wiki/SKILL.md` and `.grok/skills/llm-wiki/references/wiki-schema.md` exactly.

1. Read `wiki_policy.mode` from the platform manifest — stop if `off`.
2. Cache-first: cite policy + `wiki/index.md`.
3. Run the requested op with compress-or-skip and approval gates.
4. Never edit committed `raw/` sources; never put secrets in wiki.
