# /code-review

> Diff-scoped code review quality gate. Wires the existing strict maintainability code-review skill (code judo / file-size / spaghetti bar) together with process, PHP/MySQL/Python stack lens, and loc...

**Platform:** Cursor · same skill as Grok `/code-review` · Claude `/code-review`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Scope: working-tree | branch | PR# ; optional: deep | stack=php,mysql,python`

# Code Review

**Purpose:** Collaborative quality gate on a **diff** so the change improves overall **code health** — not perfection or gatekeeping.

**Wired skills (one flow):**

| Layer | Source | Required? |
|-------|--------|-----------|
| Process | [`docs/reference/code_review_article.md`](../../../docs/reference/code_review_article.md) + [`references/process.md`](references/process.md) | always |
| Stack risks | [`references/stack-php-mysql-python.md`](references/stack-php-mysql-python.md) | when stack matches; generic otherwise |
| **Strict maintainability** | **Existing code-review skill** → [`references/strict-maintainability.md`](references/strict-maintainability.md) (mirrors `~/.grok/skills/code-review`) | **always** |
| Local orchestrator | [`references/local-orchestrator.md`](references/local-orchestrator.md) | when template/CLI/deploy paths change |

Do **not** run a “soft” review that skips the existing strict skill. Process and stack find impact issues; the existing skill is the structural/maintainability bar.

**Cache is king.** Manifest + lean conventions before source. Diff-only by default.

**Report-only.** Do not edit application code. Do not auto-merge.

## Complements (do not duplicate)

| Skill | Role |
|-------|------|
| **Existing `code-review` (strict)** | Maintainability / code judo — **inlined** via `references/strict-maintainability.md` |
| bug-hunter-agent | Defect taxonomy / deeper hunt when many bugs |
| security-audit-agent | Auth/secrets/CDD deep pass when those paths change |
| git-workflow-guardrails | Commit/push/PR mechanics after review |
| branch-context-agent | Branch vs TODO alignment |

## Modes

| Mode | When | Behaviour |
|------|------|-----------|
| **standard** (default) | `/code-review`, `/chain code-review` | Process + stack + **full existing strict skill** + report |
| **deep** | `deep` in args | Same; bias even harder toward ambitious reframes; optional whole-module read of hot files in the diff |
| **pr** | PR number/URL | Same; frame comments for GitHub (`blocking` / `suggestion` / `nit`) |

## Phase 0 — Scope (required)

1. Resolve base: `origin/develop` or `origin/master` (prefer develop when present), else working-tree vs `HEAD`.
2. Collect file list:

   ```bash
   BASE=$(git rev-parse --verify --quiet origin/develop || git rev-parse --verify --quiet origin/master || echo HEAD)
   git -c core.quotepath=false diff --name-only "${BASE}"...HEAD 2>/dev/null || git -c core.quotepath=false diff --name-only HEAD
   ```

3. Empty diff → report "no changes" and stop (no fake findings).
4. Size gate: if hundreds of files or multi-MB diff, ask to narrow scope; do not rubber-stamp huge PRs.

## Phase 1 — Context (article: understand context first)

Load (lean):

1. Project manifest (stack, language, database_engine, paths) — MCP `get_project_manifest` when available
2. `docs/codebase/CONVENTIONS.md` section grep if large
3. `docs/codebase/CONCERNS.md` only if security/auth/payments paths in diff
4. PR/branch description or latest TODO bullet for intent

State intent in one line: *what the change claims to do*.

## Phase 2 — Systematic review (article + stack)

Order by impact:

1. **Correctness & design** — matches intent? architecture fit?
2. **Stack risks** — [`references/stack-php-mysql-python.md`](references/stack-php-mysql-python.md)
3. **Security** — injection, secrets, authz; names not values
4. **Tests** — critical paths (auth, money, integrity) covered?
5. **Local orchestrator** — [`references/local-orchestrator.md`](references/local-orchestrator.md) when template/CLI/deploy paths change

Do not flood style nits (linters own those).

## Phase 3 — Existing code-review skill (strict maintainability) — **required**

**Always load and apply** [`references/strict-maintainability.md`](references/strict-maintainability.md).

That file **is** the existing Grok code-review skill (strict code quality / code judo). Apply its:

- Core prompt (ambitious structural simplification)
- Non-negotiable standards (1k-line files, spaghetti growth, design bias, thin wrappers, type/boundary cleanliness, canonical layer, atomic updates)
- Primary review questions
- What to flag aggressively
- Preferred remedies
- Approval bar and **presumptive blockers**

Map findings:

| Strict skill bar | Report severity |
|------------------|-----------------|
| Presumptive blockers (1k-line cross, spaghetti branches, wrong-layer leak, missed code-judo when path is clear, etc.) | `blocking` or `high` (REQUEST_CHANGES if unaddressed) |
| Other structural / abstraction issues | `high` or `important` |
| Tone / phrasing from existing skill | Prefer its good phrases |

If the user skill at `~/.grok/skills/code-review/SKILL.md` is newer than the project mirror, prefer the stricter of the two and note drift in the report.

## Phase 4 — Constructive feedback

For every finding:

- **Severity:** `blocking` | `high` | `important` | `nit`
- **File:line** (right-side / new file line when possible)
- **What** + **why**
- **Suggestion** (concrete; prefer existing skill remedies for structural issues)
- Labels: `blocking:`, `suggestion:`, `nit:`

Stack-style examples:

- “This query is built with string concatenation — switch to a prepared statement.”
- “N+1 risk: use with() / select_related / joinedload.”

Strict-skill-style examples:

- “this pushes the file past 1k lines. can we decompose this first?”
- “i think there's a code-judo move here that makes this much simpler…”

Avoid: “Fix this”, personal attacks, pure style nits when security/structure issues exist.

## Phase 5 — Verdict (combined bar)

Approve only when **both** hold:

1. **Article code-health bar** — change improves overall health; no open process/stack **blocking** items (injection, secrets, authz, critical tests, unsafe multi-write, wave reintro, destructive CLI without dry-run).
2. **Existing skill approval bar** — no clear structural regression, no unjustified 1k-line explosion, no obvious spaghetti growth, no missed obvious code-judo when path is visible, no architecture-boundary leak / helper duplication (see strict-maintainability.md).

| Verdict | When |
|---------|------|
| **APPROVE** | No open blocking from either layer; remaining notes are suggestions/nits |
| **REQUEST_CHANGES** | Any `blocking` from stack **or** existing strict skill |
| **COMMENT** | No blockers but material high/important items or unclear intent |

## Phase 6 — Report artifact

Write:

```text
reports/reviews/YYYY-MM-DD-code-review.md
```

Use [`references/report-template.md`](references/report-template.md). Include sections for stack findings **and** strict-maintainability findings.

Handoff (≤80 tokens):

```markdown
code_review: verdict=…; blocking=N; high=N; files=M; strict_skill=applied
security_followup: yes|no
stack_lens: php,mysql,python|generic|template
```

## Anti-patterns

- Running process/stack review **without** the existing strict skill pass
- Rubber-stamping without reading the diff
- Softening existing-skill blockers into nits
- Whole-codebase scan when user asked for diff review
- Auto-fixing or recommending fleet wave deploy

## Local install model

Apps get this skill via `orchestrator upgrade` (per-app). The strict bar ships as `references/strict-maintainability.md` so apps do not depend on `~/.grok`. Keep that file in sync when the user skill improves.

## Related

- Existing skill mirror: [`references/strict-maintainability.md`](references/strict-maintainability.md)
- Process: [`references/process.md`](references/process.md)
- Stack: [`references/stack-php-mysql-python.md`](references/stack-php-mysql-python.md)
- Article: `docs/reference/code_review_article.md`
- Agent: `.grok/agents/code-review.md`
- Chain: `/chain code-review`

User focus (optional): use any extra chat text as $ARGUMENTS.
