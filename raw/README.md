# Raw sources (immutable)

**LLM agents must never edit files under this tree** after they are committed as sources.

Drop new material here, then run `/chain wiki-ingest` (or `/llm-wiki ingest`).  
Compiled synthesis lives in `wiki/` (LLM-owned).

| Subdir | Use |
|--------|-----|
| `research/` | Papers, gists notes, vendor docs |
| `sessions/` | Optional human-exported notes |
| `evidence/` | Snapshots, CI snippets, PR notes (no secrets) |

See `wiki_policy` in the project manifest and `reports/research/llm-wiki-karpathy-plan.md`.
