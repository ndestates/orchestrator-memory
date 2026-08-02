# Vault Graph Evolution Plan — Full Node Taxonomy + Self-Learning + Optional DB

**Date:** 2026-07-07  
**Scope:** Extend the self-building knowledge vault from simple lesson ledger to a richer "brain-like" graph supporting complex reasoning, precedents, codebase knowledge (template + wave apps), and self-improvement. Keep lean/file-first by default. Add optional DB backend as opt-in (price point for downstream products).  
**Repo class:** template  
**Principles:** Manifest-first, cache-first, lean tokens, L1 report-only (human gates), secure (hash-chain, scrub), non-destructive wave deploys (current branch, respect customs), multi-AI portable (synced skills + persistent context).  
**Current baseline:** 32 events. Lane 2 active: find_precedents + judgment + reasoning_chain (depth 3 traces), hybrid similarity, vault_query.py CLI + auto_hint, --build-chain/--hint support. In-memory traversal pure stdlib.

## Full Node Taxonomy (Proposed)

Nodes are events in the graph. Each has:
- `id`: content_hash (short + full for integrity)
- `type`: from taxonomy
- `area`: primary facet (reasoning, code, deploy, security, learning, multi_ai, wave, etc.) — supports "expand nodes to selected areas"
- `payload`: structured (text + fields like error_signature, fix_description, reasoning_steps[], evidence[], confidence, files[], wave_app_id)
- `parents`: list of hashes (causal/dependency edges)
- `relations`: optional richer edges (e.g., [{"type": "solves", "target": "hash"}, {"type": "analogous_to", "target": "hash", "similarity": 0.85}])
- `metadata`: ts, git_commit, source (report|loop|backfill|user|wave_app), tags, version

### Core Taxonomy (Hierarchical, Brain-Like)

**1. Foundational / Perception (raw input)**
- `raw_event`: from reports, git, user input, errors (e.g., stack traces, log lines)
- `observation`: extracted fact (e.g., "error X in wave app Y")

**2. Knowledge / Memory (accumulated)**
- `concept`: definition or principle (e.g., "compound_learning")
- `pattern`: recurring structure (e.g., "non_destructive_deploy")
- `lesson`: atomic learning (current "lesson" type, generalized)
- `precedent`: specific past instance with outcome (error + fix)
- `codebase_knowledge`: from acquire or scan (architecture, structure, stack, concern)
- `wave_app_profile`: per-wave knowledge (lessons, customizations, status from fleet)

**3. Reasoning / Thinking (complex, "brain-like")**
- `hypothesis`: proposed explanation ("this error is like previous Z")
- `reasoning_step`: single step in thought process (with input/output)
- `reasoning_trace`: full chain/tree (parents form the trace; supports tree-of-thoughts)
- `analogy`: mapping between situations ("wave deploy failure analogous to local branch issue")
- `decision`: choice made + rationale
- `evidence`: supporting data for reasoning
- `synthesis`: higher-order output (meta-pattern, proposal)

**4. Action / Solution (doing)**
- `problem`: error, bug, issue, gap (with signature for similarity)
- `solution`: fix, mitigation, implementation
- `action`: step taken (e.g., code change, deploy)
- `outcome`: result (success/failure metrics, follow-up lessons)

**5. Meta / Self-Learning (improvement)**
- `self_improvement`: how the system learned (e.g., "added error/fix pair after incident")
- `meta_pattern`: pattern across patterns
- `query_result`: stored "vault said X for query Y" for reuse
- `feedback`: user/AI outcome on a synthesis (positive/negative to refine)

**Areas/Facets** (for node expansion + targeted queries):
- `reasoning`: complex thinking, chains
- `code`: patterns, architecture, changes
- `deploy`: wave, branch, non-destructive
- `security`: concerns, scrubbing, audits
- `learning`: compound, synthesis, precedents
- `multi_ai`: cross-model persistent context
- `wave`: app-specific + fleet
- `process`: loops, chains, reports, EOD

Relations (beyond parents for DAG):
- solves / solved_by
- analogous_to (with similarity score)
- refines / generalizes
- depends_on / enables
- contradicts
- from_wave_app
- evidence_for
- next_step

This taxonomy supports "complicated thinking": e.g., error node -> linked reasoning_trace -> solution -> outcome -> new lesson. Synthesis can traverse for "similar + how fixed".

## Remaining Self Learning (Beyond Current)
Current: Lessons from loops -> graph -> synthesis for proposals/precedents. Backfill for waves. Load in sessions. Post-compound always emits.

**Gaps to close for full self-learning:**
- **Automatic precedent hinting in code tasks:** When /orchestrator or code skills get a task (e.g., "fix error X"), auto-query vault for similar (by error_signature or description) and inject as context/hints. (Not just manual synthesis.)
- **Reasoning capture:** Emit not just final lessons but intermediate reasoning (from orchestrator planning, multi-lane, perspective passes).
- **Cross-wave + fleet synthesis:** Template graph has fleet overview; wave apps build own but can "subscribe" or query shared meta.
- **Outcome feedback loop:** After actions, capture results as new nodes (success metrics, follow-up lessons). Close the loop beyond L1.
- **Query interface:** Richer than current synthesis — e.g., "find precedents for this error in wave apps' codebases", "build reasoning chain for similar problems", "suggest improvements based on past fixes".
- **Scalability for complex graphs:** Current JSONL fine for lean; but for large (many waves, deep reasoning) need better traversal/indexing.
- **Multi-model persistence:** Already via files + synced skills, but ensure vault queries work in Claude Projects / Copilot / Gemini Gems.
- **Self-expansion:** Auto-detect areas from new events; grow taxonomy.
- **Verification/Integrity at scale:** Extend verify_ledger for richer relations.

This closes "self learning" for the template and waves: each app's vault becomes a living "brain" of its history + template meta, queryable for better decisions.

## Plan to Extend Node Model and Synthesis (Shape B — Multi-Lane Parallel)

**Shape:** Multi-lane (parallel where possible: model extension independent of DB opt-in and wave integration). Lanes: 1. Taxonomy+Model, 2. Synthesis+Query, 3. DB Opt-In Layer, 4. Backfill+Wave+Reports Expansion, 5. Integration+Docs+Verification. Merge at "full self-learning demo".

**Phases:**
- Phase 0: Manifest + current state (done in this session).
- Phase 1: Planning + taxonomy definition (this plan).
- Phase 2: Core extensions (model, synthesis).
- Phase 3: Optional DB + opt-in.
- Phase 4: Expansion + integration.
- Phase 5: Docs, tests, wave safety, verification.

**Execution Steps (in order; some parallel):**

### Lane 1: Node Model Extension (Core Taxonomy)
- **Step 1.1 (agent: data-architect-expert or python-expert):** Extend `scripts/_engine/vault.py` make_event/emit_event to support full taxonomy. Add `area`, `relations` list, richer payload schemas (use JSON schema or docstrings for validation). Default to current for backward compat.
  - Files: `scripts/_engine/vault.py` (new functions: `make_rich_event`, `add_relation`).
  - Risk: low (additive). Tokens: low.
  - Acceptance: Old events load; new nodes have area/relations; tests pass.
  - **Status (2026-07-07):** Done. make_event/emit support area+relations+extra; added make_rich_event, add_relation; emit_reasoning/error/fix + new: precedent, problem, codebase_knowledge, outcome, synthesis. 
- **Step 1.2:** Update `build_simple_graph` and loaders to handle new fields.
  - **Status:** Done (includes relations edges; verify checks relation targets).
- **Step 1.3:** Add `emit_reasoning_event`, `emit_error_event` etc. helpers.
  - **Status:** Done + expanded. Synthesis and backfills use them. Ledger has area/relations populated (demo nodes + future emits).

### Lane 2: Synthesis + Query Enhancement (for Reasoning + Precedents)
- **Step 2.1 (agent: python-expert-agent):** Extend `vault_synthesis.py`:
  - Support `--area` filter, `--build-reasoning-chain` (traverse parents + relations for "how we fixed").
  - Improve `find_similar` (beyond difflib: keyword overlap + type/area match; optional simple embedding if lean).
  - New: `find_precedents(query, area="error")` -> similar errors + fixes + reasoning traces + "same or similar?" score.
  - Auto "hint" mode: if query looks like error/code task, return precedents.
  - Files: `scripts/_engine/vault_synthesis.py`, new `vault_query.py`.
  - Risk: medium (query logic). Tokens: medium.
  - **Status (2026-07-07):** Done. Hybrid scoring in find_similar; find_precedents + judgment + linked_fixes; build_reasoning_chain (parents+reverse relations, pure stdlib); auto_hint_for_task + --hint/--build-chain in both synthesis and new vault_query.py. CLI demos produce depth-3 chains (error->fix->synthesis).
- **Step 2.2:** Integrate simple graph DB in-memory (dicts + networkx? No — keep pure stdlib or add optional). For complex: use in-memory for synthesis.
  - **Status:** Done (build_simple_graph + reverse index in build_reasoning_chain use dicts/sets/lists only).
- **Step 2.3:** Add CLI for "vault query 'error msg'".
  - **Status:** Done (vault_query.py main + synthesis flags; `python3 scripts/_engine/vault_query.py --query "..." --build-chain --hint`).

### Lane 3: Optional DB Backend (Price Point, Deploy Simple First)
- **Step 3.1 (agent: data-architect-expert):** Keep JSONL as default (simple, no deps, git-friendly, wave-safe).
  - Add optional SQLite backend (embedded, file-based, no server — `vault.db` alongside JSONL or replace for query).
  - Schema: mirror events + indexes on type/area/hash + FTS for text search.
  - In `vault.py`: pluggable backend (if manifest `vault_backend: sqlite` use sqlite else jsonl).
  - Sync: on emit, write to both (or migrate).
  - Files: `scripts/_engine/vault_sqlite.py` (new), update `vault.py`.
  - Risk: medium (DB code). Tokens: low.
- **Step 3.2:** Manifest opt-in: add to `paths` or new `vault` section: `backend: jsonl | sqlite`, `db_path`.
  - In individual project: set in `.grok/project-manifest.yaml` or `.github/...`. Default jsonl.
  - Price point: Document in `docs/reference/manifest.md` and `TEMPLATE_ADOPTION.md`: "JSONL (core, free in template). SQLite (advanced queries, full-text, complex reasoning) — opt-in for commercial products; consider as premium tier (extra cost for users of your product)".
  - Deploy: simple way first (JSONL always). DB only if opted (scripts check manifest; scaffold creates .db only if sqlite).
  - Wave: respect — backfill to current branch; if app opts sqlite, their deploy can include it (non-destructive).
- **Step 3.3:** Migration: `vault-migrate.py` jsonl <-> sqlite.
- **Step 3.4:** In synthesis/query: use DB for speed if enabled.

### Lane 4: Backfill + Wave + Reports/Codebase Expansion (Self-Learning + Wave Codebases)
- **Step 4.1:** Extend `scripts/backfill-vault-from-reports.py` (and inline in deploy scripts) to use full taxonomy. Parse reports for richer nodes (e.g., extract "error" from "failure" sections, "fix" from resolutions, "reasoning" from executive summaries).
  - For codebase: parse `docs/codebase/*` + run acquire if stale; emit `codebase_knowledge` + `code_pattern` nodes.
  - For wave codebases: enhance backfill-wave-vault.sh to (optionally) pull from wave's `docs/codebase` (if accessible) or fleet reports; emit `wave_codebase` + app-specific. Always current branch, non-overwrite.
  - Add "self learning" nodes: after expansion, run synthesis and emit `meta_pattern` / `self_improvement`.
  - Files: update backfill scripts, new parsers in `_engine`.
  - Risk: medium (parsing). Tokens: low.
- **Step 4.2:** Update `deploy-loops-starter-wave.sh` and `backfill-wave-vault.sh` to call new backfill + post-check (verify + sample query).
- **Step 4.3:** For waves: ensure scaffold + backfill always include check step ("once deployed it also needs to check" — run verify + basic synthesis).

### Lane 5: Integration, Docs, Verification (Full Self-Learning)
- **Step 5.1 (agent: orchestrator):** Integrate vault query into `orchestrator-v2.md` and `load-project-cache-first`: if task involves code/error/deploy, auto-query vault for precedents and inject as "hints" (e.g., "Similar precedent: ... fixed by ...").
  - Update session-start chain to load relevant subgraph.
  - Files: `.grok/prompts/orchestrator-v2.md`, load scripts, chains.
- **Step 5.2:** Update docs per outline (knowledge-vault.md already has some; expand with taxonomy, DB opt-in, examples of reasoning queries, wave self-learning).
  - Add to `docs/codebase/ARCHITECTURE.md`, `CONCERNS.md`, `documentation.md`.
  - New: `docs/reference/vault.md`.
- **Step 5.3:** Verification:
  - Run full link audit (`scripts/docs-link-audit.py`).
  - Test synthesis queries for complex reasoning.
  - Wave dry-run simulation (current branch, no overwrite).
  - Update `reports/docs/.doc-outline-...` and gap report.
  - Add to loop/chain audits.
- **Step 5.4:** Remaining self-learning:
  - Feedback: after synthesis use, capture outcome as new node.
  - Auto-expansion: on new report, trigger backfill.
  - Cross-model examples in multi-AI docs.
  - Price point doc: "For products built on this: JSONL core (included). SQLite advanced (extra tier for users needing complex graph queries/reasoning search)."

**Merge Gates:**
- After Lane 1+2: basic extended model + synthesis works on existing + new nodes.
- After Lane 3: DB opt-in works, simple JSONL still default.
- After Lane 4+5: wave deploys safe, full self-learning (auto-hints, precedents for code) demo'd, docs updated.

**Risks & Mitigations:**
- Token bloat: enforce summaries, opt-in subgraphs, lean defaults.
- Complexity: keep JSONL primary; DB optional.
- Wave blast: test non-destructive on current branch; use existing guards.
- Security: extend scrub/verify for new fields.
- Adoption: document price point clearly; simple deploy first.

**Timeline / Agents:**
- Use `/orchestrator` or multi-lane for execution.
- Agents: python-expert (model/synthesis), data-architect (taxonomy/DB), documentation-specialist (docs), github-expert (wave/deploy), test-safety (verify).
- Budget: keep under loop-budget; L1 for reports.

**Evidence / Citations:**
- Current: `reports/vault/events.jsonl` (28 events), `scripts/_engine/vault.py`, `vault_synthesis.py`, `backfill-vault-from-reports.py`, `knowledge-vault.md`, `docs/codebase/ARCHITECTURE.md`, `CONCERNS.md`, `TODO/2026-07-06_TODO.md`, manifest (vault paths, compound_learning).
- Prior: fleet audit, multi-AI plan, wave deploy policies.

This plan extends to full self-learning: the vault becomes a living "brain" of reasoning + precedents, with DB as optional premium for advanced use. Simple JSONL deploys first for all (including waves). Individual projects opt-in DB via manifest (price point for your product's users).

Ready to execute? Run `/orchestrator <this plan>` or specific lane.
