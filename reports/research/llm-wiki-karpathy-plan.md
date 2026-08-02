# LLM Wiki (Karpathy) — Orchestrator Phase 0 plan

**Status:** Phases 0–4 implemented on template (scaffold → session/MCP → lint watch → guide)  
**Branch:** `feature/llm-wiki-phase0-2026-07-15`  
**Date:** 2026-07-15  
**Source idea:** [Andrej Karpathy — llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (gist `442a6bf555914893e9891c11519de94f`)

---

## 1. Executive summary

Karpathy’s **LLM Wiki** pattern treats knowledge as a **persistent, compounding markdown artifact** maintained by the LLM, not as RAG over raw files on every question.

Orchestrator already implements the same philosophy for **code context** (`docs/codebase/` + lean cache) and **machine learning** (`reports/vault/events.jsonl` + compound). What we lack is a first-class **human-navigable synthesis layer** for multi-source judgment (research, decisions, filed query answers).

**Phase 0** froze policy and manifest keys. **Phase 1** adds `wiki/` + `raw/`, `/llm-wiki`, chains, deploy selection `wiki`, tests, and pilot ingest (Karpathy notes + vault snapshot).

---

## 2. Pattern recap (normative)

### Three layers

| Layer | Role | Orchestrator mapping (target) |
|-------|------|-------------------------------|
| **Raw sources** | Immutable inputs; LLM never edits | `raw/` (or `paths.wiki_raw_dir`) |
| **Wiki** | LLM-owned markdown: summaries, concepts, decisions, index, log | `wiki/` (or `paths.wiki_dir`) |
| **Schema** | Agent conventions for ingest / query / lint | skill + schema prompt + manifest `wiki_policy` |

### Three operations

| Op | Meaning | Default risk level |
|----|---------|-------------------|
| **Ingest** | Source → summary + update related pages + index + log | Medium (multi-file write); L1 propose + human approval |
| **Query** | Answer from wiki first; optional **file-back** of good answers | Low–medium |
| **Lint** | Contradictions, stale claims, orphans, missing concepts | L1 report-only |

### Supporting files (Karpathy)

- **`index.md`** — content catalog (category + one-line summary per page)  
- **`log.md`** — append-only ops timeline; prefer parseable prefixes  
  `## [YYYY-MM-DD] ingest|query|lint | Title`

### Optional later

- Search CLI / MCP when index outgrows ~100 pages (rg first; no new deps without approval)  
- Obsidian as human IDE; git as source of truth  

---

## 3. What we already have (do not replace)

| Asset | Role | Keep? |
|-------|------|-------|
| `docs/codebase/*` | Lean **code** cache; dense maps for greppable systems | **Yes — code path** |
| `SECTIONS.md` / README index | Section index before deep read | Yes |
| `reports/vault/events.jsonl` | Hash-chained lessons, scrub, provenance | **Yes — machine ledger** |
| `STATE.md` / `VISION.md` / TODO | Session spine | Yes |
| Compound + loop-verifier | Maker/checker + lesson capture | Yes |
| L1 watches (cache-freshness, vault-integrity, …) | Automated health | Yes; wiki-lint becomes a sibling later |

**Product model (three surfaces):**

```text
docs/codebase/     → code orientation (dense, greppable-friendly)
wiki/              → multi-source judgment & research (Karpathy layer)  [Phase 1+]
reports/vault/     → integrity + compound graph (not a browsable wiki)
```

---

## 4. Decisions locked in Phase 0

### D1 — Scope order

1. **Template meta-knowledge first** (orchestrator product concepts: vault, cache, chain, loop, install).  
2. **Per-app optional** via deploy selection / `wiki_policy.mode` — never fleet-default.  

### D2 — Code vs wiki

- **Code facts** stay in `docs/codebase/` (and source).  
- **Wiki is for** multi-source synthesis, research, decisions, open questions, filed query answers.  
- **Compress-or-skip rule:** create a wiki page only if it compresses facts from **≥2 sources** or from non-greppable narrative. Never mirror a small greppable file into a longer page.  

*Rationale:* community A/B (code “entity wiki”) showed entity sprawl can cost *more* tokens than grep; dense maps win for code.

### D3 — Autonomy (L1 default)

| Action | Allowed without human? |
|--------|------------------------|
| Query (read wiki + answer) | Yes |
| Lint report | Yes (report-only) |
| Ingest propose (diff / draft pages) | Yes |
| Commit wiki writes / multi-file apply | **No** — approval gate (aligns `agent_policy.require_approval_for_medium_risk`) |
| Auto-ingest every PR / chat turn | **No** |

### D4 — Dual-write with vault

Successful accepted ingests **emit vault events** (scrubbed, hashed) so compound/session-start brain stays coherent. Wiki ≠ vault; vault remains the integrity substrate.

### D5 — Token policy

- Session-start must **not** load the whole wiki.  
- When `wiki_policy.mode` ≠ `off` and wiki exists: load at most **index headings / last log lines / open questions** (capped; see manifest).  
- Wiki pages count against a **separate** cap (`max_wiki_pages_per_session`), not `max_cache_files_default` for `docs/codebase`.  

### D6 — Mode enum

| `wiki_policy.mode` | Meaning |
|--------------------|---------|
| `off` | No wiki ops; paths may still exist unused; no session-start wiki load |
| `lean` | **Template Phase 1 default.** Index + log + capped page reads; L1 ingest propose |
| `full` | Future: richer entity/concept trees; still no auto-commit |

---

## 5. Target layout (Phase 1 — created on template)

```text
raw/                      # immutable sources (LLM never edits)
  research/
  sessions/
  evidence/
wiki/
  index.md
  log.md
  sources/                # one summary per ingested source
  concepts/
  entities/               # only multi-source / non-greppable
  decisions/              # decision + rationale + reversal conditions
  queries/                # filed-back answers
  contradictions.md
  open-questions.md
```

Schema (Phase 1): `.grok/skills/llm-wiki/` + schema prompt; chains `wiki-ingest`, `wiki-query`, `wiki-lint`.

---

## 6. Manifest draft (Phase 0 — keys present, mode off)

Canonical: `.github/project-manifest.yaml` (synced to platforms).

### `paths` (new)

| Key | Default | Purpose |
|-----|---------|---------|
| `wiki_dir` | `wiki` | LLM-maintained wiki root |
| `wiki_raw_dir` | `raw` | Immutable sources |
| `wiki_index` | `wiki/index.md` | Content catalog |
| `wiki_log` | `wiki/log.md` | Ops log |

### `wiki_policy` (new block)

| Key | Default | Purpose |
|-----|---------|---------|
| `mode` | `lean` (template) | off \| lean \| full |
| `enabled` | derived: mode ≠ off | Convenience for agents |
| `l1_report_only` | `true` | Lint/ingest propose; no auto-commit |
| `require_approval_for_writes` | `true` | Human gate for multi-file apply |
| `compress_or_skip` | `true` | Enforce ≥2-source / non-greppable rule |
| `max_wiki_pages_per_session` | `2` | Cap page reads after index/log |
| `session_start_load` | `index_log_only` | index headings + log tail + open-questions only |
| `dual_write_vault` | `true` | Emit vault events on accepted ingest |
| `deploy_selection` | `wiki` | Future deploy-bundle selection name |
| `auto_ingest` | `false` | Never batch-ingest without ask |

Agents **must** honor `mode: off` on apps that have not enabled wiki. Template Phase 1 uses `lean`.

---

## 7. Phased roadmap (post–Phase 0)

| Phase | Outcome |
|-------|---------|
| **0** | Policy locked; manifest keys; CONCERNS; research memo — **done** |
| **1** | Scaffold `wiki/` + `raw/`; skill + schema; chains; tests; pilot ingest — **done** |
| **2** | session-start lean hook; eod optional file-back; research-deep-dive → wiki; MCP read tools — **done** |
| **3** | `wiki-lint-watch` L1 (manual); `wiki_lint_check`; confidence labels — **done** (role split deferred) |
| **4** | Deploy selection `wiki`; guide + README — **done** |

---

## 8. Non-goals (Phase 0–2)

Explicitly **out of scope** until a later approved phase:

1. Embedding / vector RAG as the primary retrieval path for the wiki  
2. Entity-per-source-file wiki for application code (use code cache)  
3. Fleet wave auto-deploy of wiki content across apps  
4. Auto-ingest of all chats, PRs, or CI logs  
5. Replacing vault ledger with wiki pages  
6. New mandatory dependencies (qmd, Obsidian plugins, etc.) without approval  
7. Multi-repo “sync all wikis” at session-start  

---

## 9. Risks (see also CONCERNS §13)

| Risk | Mitigation |
|------|------------|
| Token bloat / double-read wiki+source | Trust-at-query **or** verify-on-demand — not both by default; compress-or-skip |
| Stale wiki after code moves | Code facts live in code cache; wiki lint for multi-source pages only |
| Secrets in raw/wiki | Secrets guard + vault scrub patterns; never commit keys |
| Second brain drift vs vault | Dual-write; vault remains canonical for lessons integrity |
| Skill sprawl | One skill + three chains; single schema file |
| False confidence | Query packets may use strong/moderate/weak labels (Phase 3) |

---

## 10. Success metrics (Phase 1 pilot eval)

| Metric | Target |
|--------|--------|
| Fixed research queries (3) | Wiki path ≤50% tokens vs re-reading full raw set |
| Page quality | No page longer than its primary source without multi-source merge |
| Session-start | Still lean; wiki load ≤ log tail + index section |
| Human acceptance | Operator does not mass-delete pilot pages |
| Vault coherence | Every accepted ingest has a matching vault event |

---

## 11. Acceptance checklists

### Phase 0

- [x] Research memo committed  
- [x] Manifest `paths` + `wiki_policy` drafted  
- [x] Platform manifests synced  
- [x] `docs/reference/manifest.md` documents keys  
- [x] `docs/codebase/CONCERNS.md` §13  
- [x] Guides index points to this memo  

### Phase 1

- [x] `wiki/` + `raw/` scaffold + pilot pages  
- [x] Skill `/llm-wiki` + schema + prompt  
- [x] Chains `wiki-ingest`, `wiki-query`, `wiki-lint`  
- [x] Deploy selection `wiki` (not default)  
- [x] Tests `tests/test_llm_wiki_scaffold.py`  
- [x] Template `wiki_policy.mode: lean`  

### Phase 2–4

- [x] `session-wiki-brief.py` + session-start / standup wiring  
- [x] EOD optional file-back; research memo → wiki offer  
- [x] MCP `wiki_status` / `wiki_search_index` / `wiki_read_page` + sandbox `wiki`/`raw`  
- [x] `wiki_lint_check.py` + host + `wiki-lint-watch` pattern/chain  
- [x] Confidence labels in skill/schema  
- [x] Guide + README + CHANGELOG  
- [ ] Optional: schedule wiki-lint on Mondays (needs loop-audit + human approval)  
- [ ] Optional: dedicated retriever/updater agent roles  

---

## 12. References

- Karpathy gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f  
- Orchestrator vault: `docs/guides/knowledge-vault.md`, `docs/guides/vault-learning-expansion.md`  
- Cache spine: `docs/codebase/README.md`, `docs/guides/cache-and-token-savings.md`  
- VISION: compound learning + cache-first north star  

## Related research in this repo

- `reports/research/loop-engineering-14-step-roadmap.md` — systems that prompt agents  
- `reports/research/prompt-patterns.md` — grounded RAG refusal patterns (orthogonal; wiki is not RAG-first)  
