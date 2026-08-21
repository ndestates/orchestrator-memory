# STORM-Inspired Patterns Plan (No STORM Adoption)

[UPDATED 2026-07-07]

**Branch:** `feature/storm-inspired-patterns-2026-06-19`  
**Status:** Phase D complete (guardrails + perspective-guided-discovery pattern); Phase E pending  
**Source reviewed:** [Nav Toor X article](https://x.com/heynavtoor/status/2067194761446920264) / [Stanford STORM](https://github.com/stanford-oval/storm)

## Decision

We **borrow patterns**, not the STORM product. No `knowledge-storm`, no DSPy, no Bing/search APIs, no viral copy-paste prompts.

| Borrow | Reject |
|--------|--------|
| Multi-perspective questioning before writing | Open-web Wikipedia pipeline |
| Outline-first → evidence populate → polish | Long cited articles as default output |
| Structured discourse (moderator + experts + human) | Co-STORM runtime / mind-map dependency |
| Optional external research memo | STORM as default session entry |

Aligns with manifest: `cache_first_mandatory`, `no_source_until_confirmed`, `grep_before_read`, chain opt-out.

Example: Use perspectives when documenting the secure vault graph (see guides/knowledge-vault.md) — lenses include Security (hashing/scrubbing), Operator (deployment), Developer (synthesis usage).

---

## Plan 1 — Perspective pass (acquire + documentation skills)

### Goal

Before investigation or doc writing, run a **fixed lens pass** so agents ask better questions — not one flat “scan the repo” prompt.

### Lenses (default four)

| Lens | Asks |
|------|------|
| **Developer** | Structure, conventions, testability, local runtime |
| **Operator** | Deploy, CI, observability, rollback, env config |
| **Security** | Auth, secrets surface, data safety, supply chain |
| **Product / stakeholder** | User flows, scope, TODO intent vs reality |

Optional fifth lens for app repos: **Compliance** (CDD, consent, audit) — only when `stack.uses_database` or e-sign signals in cache.

### `acquire-codebase-knowledge` changes

**Insert Phase 1.5: Perspective pass** (after scan + intent read, before Phase 2 investigate).

```
Phase 1.5 output (in agent response + optional reports/codebase/.perspective-pass.md):
- Per lens: 3–5 questions (max 20 total)
- Tag each: answerable-from-cache | needs-source-read | [ASK USER]
- Cross-lens conflicts (e.g. security vs product speed)
```

**Phase 2** uses perspective questions as the investigation agenda (maps to `references/inquiry-checkpoints.md`).

**Phase 3** outline order unchanged; each doc section cites which lens drove it.

### `documentation-specialist` changes

**Insert Phase 2.5: Doc outline from perspectives** (after cache load, before Layer A site build).

```
1. Emit docs/index.md section outline (hub + guides + reference)
2. Per page: audience lens, prerequisites, verify step
3. Mark pages that need [ASK USER] before writing
```

**Layer A** writes pages from outline only (outline-first populate).  
**Layer B** cache files cross-link to human pages; no duplicate prose.

### Files to touch (Plan 1 implementation)

| File | Change |
|------|--------|
| `.grok/skills/acquire-codebase-knowledge/SKILL.md` | Phase 1.5 + checklist |
| `.grok/skills/acquire-codebase-knowledge/references/perspective-lenses.md` | **New** — lens definitions + question stems |
| `.grok/skills/documentation-specialist/SKILL.md` | Phase 2.5 + outline contract |
| `.grok/skills/documentation-specialist/references/doc-outline-from-perspectives.md` | **New** — outline template |
| `scripts/sync_grok_to_github_claude.py` | Run after skill edits (mirror) |

### Acceptance (Plan 1)

- [ ] Running acquire skill produces ≤20 tagged questions before any optional source read
- [ ] Running documentation skill emits outline before creating `docs/**/*.md`
- [ ] `bash scripts/chain-audit.sh` still 100/100
- [ ] No new npm/pip/composer dependencies

---

## Plan 2 — `research-deep-dive` chain (external topics only)

### Goal

Optional chain for **unfamiliar domain research** before implementation — e.g. new payment provider, compliance rule, integration design.

**Not** for routine feature work or codebase onboarding (use `acquire-codebase-knowledge` / `documentation-full`).

### Trigger intents

- research before implement
- deep dive
- unfamiliar domain
- integration research
- compliance research
- architecture options

### Chain sketch (`chains/registry.yaml`)

```yaml
- id: research-deep-dive
  name: Research Deep Dive (external)
  description: Cache load → perspective Q&A → structured memo (no STORM, no default web)
  intents:
    - research before implement
    - deep dive
    - domain research
    - integration research
  token_tier: medium
  max_steps: 4
  cache_files_required:
    - docs/codebase/README.md
    - TODO/
    - chains/registry.yaml
  steps:
    - id: load
      type: prompt
      invoke: load-project-cache-first
      required: true
      handoff: cache_loaded
    - id: frame
      type: skill
      invoke: research-deep-dive
      required: true
      skill_args: "phase=frame — topic from user; perspective questions; constraints from TODO/manifest"
      handoff: research_framed
    - id: gather
      type: skill
      invoke: research-deep-dive
      required: true
      skill_args: "phase=gather — user-approved sources only; mark gaps [ASK USER]"
      handoff: evidence_collected
    - id: memo
      type: skill
      invoke: research-deep-dive
      required: true
      skill_args: "phase=memo — write reports/research/<slug>-YYYY-MM-DD.md"
      handoff: research_memo_ready
```

### New skill: `.grok/skills/research-deep-dive/SKILL.md`

**Phases:**

1. **Frame** — topic, success criteria, four lenses, question list (reuse perspective-lenses.md)
2. **Gather** — answer from: (a) user-pasted sources, (b) existing cache, (c) explicit user-approved web fetch. Default: **no web**.
3. **Memo** — 1–3 page brief: decision options, risks, recommendation, open questions. Output path: `reports/research/`.

**Handoff to implementation:** suggest `/orchestrator` or domain skill (e.g. `paypal-billing-integration`) with memo path cited.

### Guardrails (Plan 2)

- Must cite `cache_loaded` + TODO branch context
- `no_source_until_confirmed` — gathering phase requires user “proceed” before web
- No secrets in memo; placeholders only
- Chain opt-out honored (`skip chain` → run frame phase only)

### Files to touch (Plan 2 implementation)

| File | Change |
|------|--------|
| `.grok/skills/research-deep-dive/SKILL.md` | **New** skill |
| `.grok/skills/research-deep-dive/references/memo-template.md` | **New** |
| `chains/registry.yaml` | Register skill + chain |
| `CHAIN.md` | One-line chain listing |
| `reports/research/.gitkeep` | **New** scaffold |
| `scripts/deploy-bundle.yaml` | Add `reports/research/.gitkeep` to scaffold_if_missing |

### Acceptance (Plan 2)

- [ ] `/chain research-deep-dive` resolves and runs 4 steps
- [ ] Memo written under `reports/research/` with evidence tags
- [ ] Chain audit passes; skill registered in `register-project-skills.py` output
- [ ] Documented in `docs/guides/chains-and-skills.md` (when Plan 1 doc pass runs)

---

## Plan 3 — Non-adoption guardrails (explicit)

### Non-goals (never add without explicit user approval)

| Forbidden | Reason |
|-----------|--------|
| `pip install knowledge-storm` / STORM repo | Wrong product; web-first |
| DSPy pipeline | New framework; token + dep cost |
| Default Bing/Tavily/Serper retrieval | Cache-first violation |
| Viral “4 copy-paste Claude prompts” | Duplicates skills/chains; no audit trail |
| Wikipedia-length auto-articles | Wrong output shape for delivery repos |
| STORM/Co-STORM branding in user-facing docs | Misleading; we use “perspective pass” |

### Required in every new artifact

1. **Cache citation** in first substantive step (`require_cache_citation`)
2. **Manifest-first** path reads
3. **Chain audit** after registry edits
4. **Content policy** — no secrets, no trade secrets (documentation-specialist rules apply to memos)
5. **Opt-out** — single-skill path documented

### Enforcement

| Check | Where |
|-------|-------|
| `bash scripts/chain-audit.sh` | CI + pre-commit on orchestrator |
| Plan 3 section in `research-deep-dive` SKILL.md | Non-goals header |
| `docs/reference/storm-inspired-patterns-plan.md` | This file (source of truth) |
| `patterns/registry.yaml` entry | `perspective-guided-discovery` pattern (Plan 4) |

### Acceptance (Plan 3)

- [ ] Non-goals block in `research-deep-dive/SKILL.md`
- [ ] No STORM-named dependencies in repo after full implementation
- [ ] Review checklist in PR template or plan § PR gates below

---

## Plan 4 — Discourse patterns → orchestrator & loops

Map STORM/Co-STORM **roles** to existing primitives — vocabulary only, no new runtime.

| STORM / Co-STORM role | Orchestrator equivalent | Already exists |
|----------------------|-------------------------|----------------|
| Moderator (probing questions) | `orchestrator` merge_gates + `contract_check` | `.claude/commands/orchestrator.md` Shape B |
| Domain experts | Specialist skills / Task subagents | `.grok/agents/`, lanes |
| Human user steering | Chain opt-out, approval gates | `chain/SKILL.md`, `agent_policy` |
| Mind map / shared conceptual space | `STATE.md` + `docs/codebase/` cache spine | LOOP.md, cache-first |
| Turn-based discourse | Chain steps + handoff JSON (≤80 tokens) | `chains/registry.yaml` |
| Verifier | `loop-verifier`, `check-work` | skills |

### New pattern file: `patterns/perspective-guided-discovery.md`

Contents:

- When to use (discovery, docs, external research)
- When **not** to use (bug fix, migration, routine CRUD)
- Flow diagram: perspectives → questions → outline → evidence → verify
- Link to Plan 1–2 skills; explicit “not STORM”

### `loop-engineering` addendum

- L1 loops stay report-only; perspective pass is **on-demand**, not scheduled
- L2+ (future): optional `research-deep-dive` output could feed `STATE.md` — gated by `allow_l2: false` today
- Daily triage does **not** auto-run research chain

### `orchestrator` command hint (optional doc-only)

Add one bullet to orchestrator planning schema:

```yaml
discovery_mode: optional  # when true, prepend perspective pass before lanes
```

Implementation: documentation in `.claude/commands/orchestrator.md` only (no code gen change in phase A).

### Files to touch (Plan 4 implementation)

| File | Change |
|------|--------|
| `patterns/perspective-guided-discovery.md` | **New** |
| `patterns/registry.yaml` | Register pattern |
| `.grok/skills/loop-engineering/SKILL.md` | Short § Perspective-guided discovery |
| `.claude/commands/orchestrator.md` | Optional `discovery_mode` note |
| `LOOP.md` | Link to new pattern |

### Acceptance (Plan 4)

- [ ] Pattern registered; `bash scripts/loop-audit.sh` passes
- [ ] Loop engineering skill cites pattern
- [ ] No new scheduled workflows

---

## Implementation phases (this branch)

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **A** (this commit) | Plan + TODO | This doc, branch TODO |
| **B** | Plan 1 | Perspective pass in two skills + reference files |
| **C** | Plan 2 | `research-deep-dive` skill + chain + scaffold |
| **D** | Plan 3 + 4 | Guardrails in skill, pattern file, loop/orchestrator docs |
| **E** | Verify | `chain-audit.sh`, `check_name_alignment.py`, sync mirrors, PR → develop |

### PR gates (each phase)

1. `python3 scripts/sync_grok_to_github_claude.py`
2. `python3 scripts/check_name_alignment.py`
3. `bash scripts/chain-audit.sh` → 100/100
4. No new dependencies

---

## Out of scope

- Integrating STORM demo UI or `storm.genie.stanford.edu`
- Auto-scheduling research loops
- Replacing `acquire-codebase-knowledge` with web research
- Wave deploy until merged to `develop`

## References

- Cache: `docs/reference/manifest.md`, `.grok/skills/chain/SKILL.md`, `.grok/skills/acquire-codebase-knowledge/SKILL.md`
- Stanford STORM paper: https://arxiv.org/abs/2402.14207 (reference only)