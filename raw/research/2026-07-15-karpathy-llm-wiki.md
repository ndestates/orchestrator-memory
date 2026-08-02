# Source: Karpathy LLM Wiki pattern

- **URL:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Captured:** 2026-07-15
- **Type:** external idea file (immutable snapshot notes for wiki ingest)
- **Internal plan:** `reports/research/llm-wiki-karpathy-plan.md`

## Core claim

Most LLM+document systems re-derive answers via RAG at query time. The LLM Wiki pattern instead **compiles** knowledge into a persistent, interlinked markdown wiki that the LLM maintains. Knowledge compounds; cross-references and contradictions are updated on ingest, not rediscovered every question.

## Three layers

1. **Raw sources** — immutable; LLM never edits.
2. **Wiki** — LLM-owned markdown (summaries, entities, concepts, index, log).
3. **Schema** — agent conventions (ingest / query / lint).

## Three operations

- **Ingest** — one source → summary + update related pages + index + log.
- **Query** — answer from wiki first; good answers may be filed back as pages.
- **Lint** — contradictions, stale claims, orphans, missing concepts.

## Supporting files

- `index.md` — content catalog
- `log.md` — append-only ops timeline with parseable prefixes

## Boundary (code repos)

Entity pages that merely mirror greppable single files can cost more tokens than grep. Prefer dense maps for code; use wiki for multi-source judgment and research.

## Non-goals for this capture

No full gist dump of third-party comments; no credentials; no executable install scripts.
