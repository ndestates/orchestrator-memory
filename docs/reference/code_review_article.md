# Code review best practices (source article)

**Used by:** `.grok/skills/code-review/` and `/chain code-review`  
**Stack focus in part 2:** PHP / MySQL / Python  
**Install model:** per-app orchestrator (local install/upgrade) — not fleet wave  

Source conversation: [Grok share](https://grok.com/share/c2hhcmQtMw_26475ec7-3287-488c-a338-b800bae3ff4f).

---

## What should happen in a code review

A code review (typically done via Pull Request or Merge Request) is a collaborative quality gate where one or more peers examine code changes before they are merged into the main codebase.

Its core purpose is to improve **code health** — catching issues early, ensuring consistency, sharing knowledge, and raising the overall quality of the system. It is not about achieving perfection or gatekeeping.

### The ideal code review flow

1. **Author prepares the change well**
   - Clear title + description explaining what changed and why.
   - Small, focused PR (ideally 200–400 lines; larger changes are harder to review effectively).
   - Tests written and passing, linters/formatters clean, self-review done.
   - Links to tickets, design docs, or context provided.

2. **Reviewer(s) understand the context first**
   - Read the PR description and any linked requirements before diving into the diff.
   - Understand the intent and the problem being solved.

3. **Systematic review happens**
   - Reviewer checks the code against a mental or shared checklist.
   - Review at a sustainable pace (&lt; 500 lines per hour, shorter focused sessions).
   - Start high-level (design/architecture) → then go deeper (logic, edge cases, tests, security).
   - Use automation (linters, formatters, basic security scans) so humans focus on high-value areas.

4. **Constructive feedback is given**
   - Comments are specific, actionable, and kind.
   - Prioritized: blocking issues first, then suggestions, then minor nits.
   - “Why” is explained, and alternatives or examples are often provided.
   - Good code is praised too.

5. **Iteration & discussion**
   - Author responds to comments (clarifies, pushes fixes, or discusses trade-offs).
   - Reviewer re-reviews the updated parts.
   - Conversation stays respectful and focused on the code.

6. **Approval & merge**
   - The change is approved once it improves the overall code health of the system (even if not perfect).
   - Merge happens after CI passes (and sometimes after a short waiting period for additional input).

### What reviewers should look for (practical checklist)

Prioritize by impact. The most important things first:

**High-impact (often blocking or must-discuss):**

- **Correctness & functionality** — Does the code actually do what the requirements/ticket say? Are edge cases and error paths handled?
- **Design & architecture** — Is it well-designed for the system? Does it follow existing patterns? Single responsibility? Not unnecessarily complex?
- **Security** — Input validation, no hardcoded secrets, proper authentication/authorization, protection against common vulnerabilities.
- **Tests** — Are there good tests for the new/changed behavior? Do they cover edge cases?

**Important (usually worth addressing):**

- **Readability & maintainability** — Clear naming, simple logic, minimal duplication, consistent with the rest of the codebase.
- **Performance & efficiency** — Any obvious bottlenecks or wasteful patterns?
- **Error handling & resilience**

**Lower priority (often automated or nits):**

- Style, formatting, minor comments (use linters/formatters for these).

Google’s well-known guidance (widely adopted): Reviewers should generally approve once the change improves overall code health, even if it isn’t perfect. The goal is continuous improvement, not perfection.

### Best practices for participants

**For reviewers:** Assume good intent. Be specific and actionable. Focus on the code, not the person. Use labels (`suggestion:`, `nitpick:`, `blocking`). Praise good work.

**For authors:** Treat feedback as a gift. Respond promptly. Don’t take criticism personally — it’s about the code.

**For teams:** Keep PRs small. Automate style. Shared lightweight checklist. Timely thorough reviews. Mentoring and knowledge-sharing.

### What should not happen

- Rubber-stamping without real review.
- Vague or harsh feedback (“fix this”, personal attacks).
- Endless nitpicking on style when linters exist.
- Huge PRs that no one can reasonably review.
- Long delays with no activity.
- Blocking merges over personal preferences rather than real issues.

When done well, code reviews are one of the highest-leverage activities in software engineering.

---

## Stack is PHP / MySQL / Python

For a PHP / MySQL / Python stack, the **core code review process stays the same** (clear PR, understand context, systematic review, constructive feedback, iterate, approve when it improves code health).

What changes is **where reviewers focus** and the **specific risks** that are highest in this combination.

### Stack-specific priorities

#### 1. Database interactions (highest priority – shared across PHP & Python)

Almost every serious production issue in this stack involves the database. Reviewers should always verify:

- All queries are parameterized
  - PHP: PDO prepared statements or Eloquent/Query Builder (never string concatenation or mysql_query-style).
  - Python: Parameterized queries via mysql-connector, PyMySQL, SQLAlchemy, or Django ORM (never f-strings or % formatting for SQL).
- Transactions are used for any multi-statement operations that must succeed or fail together.
- Indexes exist (or are proposed) for new WHERE, JOIN, and ORDER BY columns. Complex queries should include an EXPLAIN or performance note.
- No `SELECT *`. Specific columns only.
- Schema changes come with proper migrations (and down migrations where feasible). Foreign keys, constraints, and data types are intentional.
- Connection handling is clean (no leaks, proper closing or connection pooling).

#### 2. PHP-specific checks

- Modern PHP practices: type declarations, return types, strict types (`declare(strict_types=1)`), namespaces, PSR-12 style.
- Input validation and output escaping (XSS protection with htmlspecialchars or equivalent).
- CSRF protection on state-changing endpoints.
- Error handling: exceptions preferred over silent failures; no sensitive info leaked in production error messages.
- Composer dependencies: `composer audit` clean, versions pinned reasonably, no known vulnerabilities.
- If using Laravel: N+1 queries, missing `with()`, validation rules, policies/authorization, middleware, and queue/job safety.

#### 3. Python-specific checks

- Style & static analysis: PEP 8 / Ruff / Black compliance, type hints (mypy or pyright preferred), no excessive `Any`.
- Resource management: context managers (`with`) for files, DB connections, locks.
- Security: Bandit-clean (or equivalent), no `eval`, safe deserialization, no command injection.
- ORM usage (Django / SQLAlchemy): N+1 prevention (`select_related` / `prefetch_related` or `joinedload` / `selectinload`), proper transaction boundaries, pagination or `iterator()` on large querysets.
- Dependencies: pip-audit / safety clean, locked versions (`requirements.txt` or `poetry.lock`).
- Async / concurrency (if used): proper locking, no blocking I/O in async paths, idempotent background jobs.

#### 4. Cross-language & integration concerns

Because the stack mixes PHP and Python:

- Shared data contracts (how data is written by one language and read by the other) must stay consistent.
- Error handling and logging formats should be coherent so debugging across services is possible.
- Credentials and config never hardcoded; environment variables or a secrets manager only.
- If one side calls the other (HTTP, queues, shared files), contracts, timeouts, retries, and failure modes are reviewed.

### Ready-to-use reviewer checklist for this stack

**Blocking / must fix**

- [ ] SQL injection possible? (string-built queries in PHP or Python)
- [ ] Missing transactions on multi-step writes?
- [ ] Hardcoded credentials or secrets?
- [ ] Critical path missing tests (especially around money, auth, data integrity)?
- [ ] Authorization / ownership checks missing on sensitive actions?
- [ ] Unbounded queries or clear N+1 problems?

**High priority**

- [ ] Proper input validation on all external data?
- [ ] Output properly escaped (XSS)?
- [ ] Indexes and query performance reasonable?
- [ ] Type safety / null safety handled (PHP 8+ types, Python type hints)?
- [ ] Error handling doesn’t leak sensitive info?
- [ ] Dependencies free of known vulnerabilities?

**Important**

- [ ] Clear naming and single-responsibility functions/classes?
- [ ] Consistent with existing codebase patterns?
- [ ] Migrations included and safe?
- [ ] Logging / observability adequate for production debugging?
- [ ] Resource cleanup (connections, files, locks)?

**Nice to have / nits**

- Style (automate with PHPCS / Ruff / Black)
- Minor comment improvements
- Small refactors that don’t affect correctness

### Tools that should be part of the process

- CI must run: PHPStan or Psalm + PHP_CodeSniffer, Ruff + mypy + Bandit, composer audit, pip-audit.
- Query inspection: enable query logging or require EXPLAIN notes for non-trivial changes.
- Test coverage gates on critical paths (especially anything touching money, auth, or data integrity).

### Feedback style reminder

Prefer:

- “This query is built with string concatenation — please switch to a prepared statement / parameterized query to eliminate SQL injection risk.”
- “This multi-table update should be wrapped in a transaction so we don’t leave partial state on failure.”
- “N+1 risk here: the loop will fire one query per user. Consider `with()` / `select_related` / `joinedload`.”

Avoid vague comments like “Fix the query” or pure style nits when real security or data-integrity issues exist.

---

## Template skill mapping

| Article concept | Template path |
|-----------------|---------------|
| Process flow | `.grok/skills/code-review/references/process.md` |
| Stack checklist | `.grok/skills/code-review/references/stack-php-mysql-python.md` |
| **Existing strict code-review skill** | `.grok/skills/code-review/references/strict-maintainability.md` (mirrors `~/.grok/skills/code-review`) — **always applied** |
| Local install / no wave | `.grok/skills/code-review/references/local-orchestrator.md` |
| Report shape | `.grok/skills/code-review/references/report-template.md` |
| Skill entry | `.grok/skills/code-review/SKILL.md` |
| Agent | `.grok/agents/code-review.md` |
| Chain | `/chain code-review` |
