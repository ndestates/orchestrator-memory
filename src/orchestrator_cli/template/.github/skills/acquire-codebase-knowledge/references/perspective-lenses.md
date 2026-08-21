# Perspective Lenses — Phase 1.5

Multi-lens questioning before investigation (STORM-inspired pattern; **not** STORM). Run after Phase 1 scan + intent read, before Phase 2 source investigation.

## Default lenses (always use four)

| Lens | Focus | Typical doc targets |
|------|-------|---------------------|
| **Developer** | Structure, conventions, testability, local runtime | STRUCTURE, CONVENTIONS, TESTING |
| **Operator** | Deploy, CI, observability, rollback, env config | STACK, INTEGRATIONS, CONCERNS |
| **Security** | Auth, secrets surface, data safety, supply chain | CONCERNS, INTEGRATIONS, TESTING |
| **Product / stakeholder** | User flows, scope, TODO intent vs reality | ARCHITECTURE, CONCERNS, README/TODO |

## Optional fifth lens

| Lens | When to include |
|------|-----------------|
| **Compliance** | `stack.uses_database: true` in manifest, or cache/TODO mentions CDD, consent, e-sign, audit trail |

## Question stems (3–5 per lens)

Adapt to **this repo** using Phase 1 context only (README, TODO, scan, manifest). Do not invent stack facts.

### Developer

- What are the entry points and how does a new contributor run the project locally?
- Which directories are generated vs hand-maintained?
- What test commands exist and which DB/env do they require?
- What naming or layering conventions must agents follow?
- Where do orchestrator paths (`.grok/`, `chains/`, `LOOP.md`) live if this is a template repo?

### Operator

- What CI workflows run on PR and deploy, and what gates block merge?
- How are containers/images built and where are they published?
- What env/config files exist (names only — no secret values)?
- What is the rollback or promotion path between branches?
- What scheduled jobs or loops touch production or shared state?

### Security

- Where are auth, permissions, and session/token handling implemented?
- How are secrets loaded (env, vault pattern) without documenting values?
- What data stores exist and which are test-only vs production?
- What dependency or image scanning runs in CI?
- What security rules in copilot-instructions must agents never violate?

### Product / stakeholder

- What is the stated product purpose in README/TODO vs what the code actually does?
- Which features are in scope on the active branch/TODO?
- What user-facing flows or panels exist (if app repo)?
- What open `[ASK USER]` decisions block accurate architecture docs?
- What intent-vs-reality gaps appear from TODO carry-forward?

### Compliance (optional)

- Where are consent, audit, or signing flows documented or implemented?
- What retention or PII handling patterns are visible in schema/docs?
- What compliance checks exist in CI or manual runbooks?

## Tagging rules (required on every question)

| Tag | Meaning | Phase 2 action |
|-----|---------|----------------|
| `answerable-from-cache` | Answer from scan, README, TODO, existing `docs/codebase/` | No source read yet |
| `needs-source-read` | Requires targeted file read after user direction or manifest `no_source_until_confirmed` lifted | Queue for Phase 2 reads |
| `[ASK USER]` | Requires human intent or policy | Emit in final response; do not guess |

**Cap:** max **20 questions** total across all lenses (3–5 per lens × 4 lenses fits).

## Cross-lens conflicts

After listing questions, note tensions, e.g.:

- Security (test DB only) vs Operator (prod-like staging data)
- Product (ship fast) vs Developer (full test gate)
- Compliance (audit trail) vs Developer (minimal logging)

Record in Phase 1.5 output under `## Cross-lens conflicts`.

## Phase 1.5 output format

Emit in the agent response. Optionally persist:

`reports/codebase/.perspective-pass.md` (create `reports/codebase/` if missing)

```markdown
# Perspective pass — YYYY-MM-DD

## Developer
1. [question] — `answerable-from-cache` | `needs-source-read` | `[ASK USER]`

## Operator
...

## Security
...

## Product / stakeholder
...

## Compliance (if used)
...

## Cross-lens conflicts
- ...

## Investigation priority (Phase 2)
Ordered list of question ids to resolve first.
```

## Phase 2 linkage

1. Load `references/inquiry-checkpoints.md` for template-specific questions.
2. **Merge** perspective questions into the investigation agenda — perspective questions take priority when they tag `needs-source-read`.
3. Do **not** open application source until `needs-source-read` items are listed and cache-only items are exhausted (manifest `no_source_until_confirmed`).

## Phase 3 linkage

When filling each `docs/codebase/*.md` section, add a one-line **Lens** note where helpful:

`> Lens: Operator, Security — evidence from .github/workflows/`

Do not duplicate the full question list in every doc; cite lens in section intro or Evidence block.