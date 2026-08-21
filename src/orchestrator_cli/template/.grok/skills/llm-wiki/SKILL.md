---
name: llm-wiki
description: "Karpathy-style LLM wiki: ingest raw sources into a persistent markdown wiki, query with index-first navigation, lint for contradictions/orphans/stale pages."
argument-hint: "ingest <path>|query <question>|lint|file-answer <slug> — e.g. 'ingest raw/research/foo.md'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# LLM Wiki

**Pattern:** [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)  
**Policy:** `reports/research/llm-wiki-karpathy-plan.md`  
**Schema:** [references/wiki-schema.md](references/wiki-schema.md)

## Phase 0 gate

1. Read manifest `wiki_policy.mode` and `paths.wiki_*`.
2. If `mode: off` → **stop**. Tell the user Phase 1 requires `lean` or `full`. Do not create wiki pages.
3. If wiki dir missing and mode is lean/full → offer scaffold only (create tree from plan §5); require approval for multi-file write when `require_approval_for_writes: true`.

## Cache-first (required)

- Cite: manifest `wiki_policy`, `wiki/index.md` (or note missing), latest TODO if scope-related.
- Do **not** load full `wiki/` or full `raw/`.
- Cap page reads at `max_wiki_pages_per_session` (default 2) after index/log.

## Ops

Parse `$ARGUMENTS` for verb (default: help).

| Verb | Action |
|------|--------|
| **ingest** | Read one raw source (path). Propose summary + related page updates + index + log. Apply only after approval if policy requires. Dual-write vault when `dual_write_vault` and writes accepted. |
| **query** | Read index → open ≤K pages → answer with citations. Offer **file-answer**. |
| **lint** | Report-only health: run `python3 scripts/wiki_lint_check.py` (+ optional host report). Contradictions, orphans, broken links, stale sources. Write under `reports/loops/` only if user asks for loop artifact. |
| **file-answer** | Write `wiki/queries/YYYY-MM-DD-slug.md`, update index + log. |
| **status** | Prefer `python3 scripts/session-wiki-brief.py` (or MCP `wiki_status`). Mode, index sections, last log lines, open questions. |
| **session-brief** | Same as status — for `/chain session-start` after vault brief. |

### Compress-or-skip (mandatory when `compress_or_skip: true`)

Create or expand a page **only if** it compresses **≥2 sources** or non-greppable narrative.  
Never clone a small greppable file into a longer page. Code facts → `docs/codebase/`.

### Ingest contract

1. Source must live under `paths.wiki_raw_dir` (or user explicitly designates a path and you copy/snapshot into raw first — never edit original outside raw without approval).
2. Propose file list (≤15 pages). Stop for approval when `require_approval_for_writes: true`.
3. Update `wiki/index.md` and append `wiki/log.md` with:
   `## [YYYY-MM-DD] ingest | Title`
4. If `dual_write_vault: true` and writes accepted: emit vault lesson/synthesis via existing vault scripts (`eod-vault-emit` style summary or `scripts/_engine/vault.py` helpers if available). Scrub secrets. Never put secrets in wiki.
5. Secrets: run mental + `git-push-secrets-guard` before commit; no API keys in raw/wiki.

### Query contract

1. Read `wiki/index.md` first (or MCP `wiki_search_index`).
2. Open at most `max_wiki_pages_per_session` content pages (+ index/log free if `session_start_load: index_log_only` patterns apply).
3. Cite wiki paths. **Always** label answer confidence:
   - **strong** — ≥2 wiki pages agree or one decision page with clear status accepted
   - **moderate** — single source page or partial index hit
   - **weak** — thin evidence; tell user to verify (raw or code cache)
4. Offer filing the answer back (`file-answer`).

### Lint contract (L1)

Report only unless user approves fixes:

- Broken relative links
- Orphans (no inbound from index)
- Concepts mentioned in sources without concept pages
- Raw path in frontmatter missing on disk
- Contradictions ledger stale vs new sources

## Anti-patterns

| Don't | Do |
|-------|-----|
| Auto-ingest all chats/PRs | Single-source ingest with approval |
| Entity-per-code-file wiki | Code cache dense maps |
| Full wiki dump into context | Index-first + cap |
| Edit `raw/` after commit as source | New file / new versioned raw snapshot |
| Fleet-deploy wiki without opt-in | `deploy_selection: wiki` only |

## Related

- Chains: `wiki-ingest`, `wiki-query`, `wiki-lint`
- Vault: `/chain session-start` vault brief; `docs/guides/knowledge-vault.md`
- Schema: [references/wiki-schema.md](references/wiki-schema.md)
