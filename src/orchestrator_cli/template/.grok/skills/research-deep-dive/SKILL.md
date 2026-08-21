---
name: research-deep-dive
description: "Optional external-topic research before implementation."
argument-hint: "Topic + phase: frame | gather | memo — e.g. 'PayPal webhook idempotency frame'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - web_search
  - bash
---
# Research Deep Dive

**Purpose:** Produce a **short, decision-ready research memo** for an **unfamiliar external topic** before implementation — integration choice, compliance rule, architecture option, vendor comparison.

**Not for:** routine feature work, bug fixes, or codebase onboarding → use `acquire-codebase-knowledge`, `documentation-full`, or domain skills.

## Non-goals (Plan 3 — do not adopt without explicit user approval)

| Forbidden | Reason | Use instead |
|-----------|--------|-------------|
| `pip install knowledge-storm` / STORM repo | Web-first; wrong product | This skill + `perspective-lenses.md` |
| DSPy pipeline | New framework; dep + token cost | Chain steps + handoff JSON |
| Default Bing/Tavily/Serper retrieval | Cache-first violation | Cache + user-pasted sources; web only after explicit approval |
| Viral copy-paste Claude prompts | No audit trail | Registered skills/chains |
| Wikipedia-length auto-articles | Wrong output shape | 1–3 page memo ([memo-template.md](references/memo-template.md)) |
| STORM/Co-STORM branding in user-facing docs | Misleading | "Perspective pass" / "perspective-guided discovery" |
| Application source edits | Out of scope | Hand off to `/orchestrator` or domain skill |

### Required in every research artifact

1. **Cache citation** in first substantive step (`agent_policy.require_cache_citation`)
2. **Manifest-first** path reads (`.grok/project-manifest.yaml` for Grok or platform equivalent per `docs/reference/manifest.md`)
3. **Chain audit** after `chains/registry.yaml` edits (`bash scripts/chain-audit.sh`)
4. **Content policy** — no secrets, tokens, or trade secrets in memos
5. **Opt-out** — single-skill path: `/research-deep-dive frame` without `/chain`

Pattern registry: `patterns/perspective-guided-discovery.md` · Plan: `docs/reference/storm-inspired-patterns-plan.md` § Plan 3–4

## Phase 0 — Load context (required)

1. Your platform manifest (`.grok/project-manifest.yaml` for Grok or per `docs/reference/manifest.md`) — `stack`, `paths`, `token_policy`, `agent_policy`
2. `docs/codebase/README.md`, latest `TODO/*.md`, active branch (offer switch per standup rules if stale)
3. `chains/registry.yaml` — only if recommending follow-on chains
4. Optional: `reports/codebase/.perspective-pass.md` from a prior acquire run

Cite cache files in the first substantive response.

## Phase routing

Parse `$ARGUMENTS` for **topic** and **phase** (default `frame` when invoked standalone; chain passes `phase=` via `skill_args`).

| Phase | When | Deliverable |
|-------|------|-------------|
| **frame** | Start of chain or user asks to research | Topic, success criteria, ≤20 lens questions, investigation priority |
| **gather** | After frame; user may approve web | Answered questions with evidence tags; gaps → `[ASK USER]` |
| **memo** | After gather | `reports/research/<slug>-YYYY-MM-DD.md` |

Emit: `Research deep dive: phase=<phase> topic=<slug>`

### Chain opt-out

If user says **no chain** / **skip chain** → run **frame** only; suggest continuing with `/research-deep-dive gather` and `/research-deep-dive memo` when ready.

---

### Phase frame

1. Confirm **topic** and **success criteria** (what decision the memo must support).
2. Load perspective stems from `.grok/skills/acquire-codebase-knowledge/references/perspective-lenses.md` (or bundled copy in target repo).
3. Apply four lenses; add **Compliance** only when manifest `stack.uses_database: true` or TODO mentions CDD/consent/e-sign/audit.
4. Emit 3–5 questions per lens (**max 20**). Tag each: `answerable-from-cache` | `needs-user-source` | `needs-web-approved` | `[ASK USER]`.
5. Note cross-lens conflicts and **out of scope** for this research.
6. List questions answerable from cache only — resolve those in frame before gather.

**No application source reads** in frame unless manifest lifts `no_source_until_confirmed` and user confirmed direction.

---

### Phase gather

**Default: no web.** Gather evidence from:

1. **Cache** — `docs/codebase/*`, TODO, README, copilot-instructions
2. **User-provided** — pasted docs, links, files the user supplies in session
3. **Web** — only after user explicitly says proceed / approves fetch (one URL or search scope at a time)

For each frame question, record answer or mark open. Tag evidence in a table (see memo template).

If `needs-web-approved` items remain and user has not approved web → stop with numbered `[ASK USER]` list; do not invent answers.

---

### Phase memo

1. Ensure `reports/research/` exists (create dir; gitkeep from template scaffold).
2. Slug: lowercase hyphenated topic (max 40 chars).
3. Fill [references/memo-template.md](references/memo-template.md).
4. Include **Options** (≥2 when plausible), **Recommendation**, **Risks**, **Open questions**.
5. **Implementation handoff** — suggest `/orchestrator` or specific domain skill with memo path.
6. **Wiki handoff (Phase 2, optional):** when `wiki_policy.mode` is `lean`|`full`, offer:
   - Snapshot memo into `raw/research/<slug>-YYYY-MM-DD.md` (immutable), then
   - `/chain wiki-ingest` (approval for multi-file wiki writes)
   - Do **not** auto-ingest; never put secrets in raw/wiki.

Red-team: no secrets, real tokens, or proprietary URLs with auth.

---

## Output contract

| Phase complete | User receives |
|----------------|---------------|
| frame | Question list + conflicts + cache-only answers |
| gather | Evidence table + remaining gaps |
| memo | Path to memo + 1-paragraph summary + handoff commands |

## Handoff JSON (chain steps, ≤80 tokens)

```json
{"topic_slug":"paypal-webhooks","phase":"frame","questions":12,"web_pending":false}
```

```json
{"topic_slug":"paypal-webhooks","phase":"gather","answered":10,"gaps":2}
```

```json
{"topic_slug":"paypal-webhooks","phase":"memo","path":"reports/research/paypal-webhooks-2026-06-19.md"}
```

## Anti-patterns

| Don't | Do instead |
|-------|------------|
| Run for "map this codebase" | `/acquire-codebase-knowledge` |
| Web search without approval | Ask user; use cache + pasted sources |
| Implement in this skill | Hand off with memo path |
| Copy STORM prompts from social posts | Use perspective-lenses pattern only |

## Related

- Perspective lenses: `acquire-codebase-knowledge/references/perspective-lenses.md`
- Chain: `research-deep-dive` in `chains/registry.yaml`
- Plan: `docs/reference/storm-inspired-patterns-plan.md`