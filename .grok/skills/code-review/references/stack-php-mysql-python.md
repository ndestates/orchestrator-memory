# Stack lens: PHP / MySQL / Python

Process stays the same; **focus and risks** change. Source: `docs/reference/code_review_article.md`.

Use when manifest language/framework includes PHP, Laravel, Python, or `database_engine` is mysql/mariadb. For other stacks, use the **Generic** section only.

## 1. Database (highest priority — shared)

- All queries **parameterized**
  - PHP: PDO prepared statements or Eloquent/Query Builder — never string-built SQL / `mysql_query`-style
  - Python: parameterized via connector/ORM — never f-strings / `%` for SQL
- **Transactions** for multi-statement write units
- Indexes for new WHERE / JOIN / ORDER BY (or note EXPLAIN)
- No `SELECT *` — explicit columns
- Schema via migrations (+ down when feasible); intentional FKs/types
- Clean connection handling (no leaks; pooling where expected)

## 2. PHP

- Types, return types, `strict_types`, namespaces, PSR-12
- Input validation + output escaping (XSS)
- CSRF on state-changing endpoints
- Exceptions over silent failure; no sensitive leaks in production errors
- Composer: reasonable pins; `composer audit` clean when deps change
- **Laravel:** N+1 (`with()`), validation rules, policies/authz, middleware, queue/job safety

## 3. Python

- PEP 8 / Ruff / Black; type hints preferred; avoid excessive `Any`
- Context managers for files, DB, locks
- Bandit-class issues: no `eval`, safe deserialize, no command injection
- ORM N+1: `select_related` / `prefetch_related` or `joinedload` / `selectinload`; paginate large sets
- Locked deps; `pip-audit` / safety when deps change
- Async: no blocking I/O in async paths; idempotent jobs

## 4. Cross-language integration

- Shared data contracts stay consistent across PHP ↔ Python
- Coherent logging/errors for cross-service debug
- Credentials only via env / secrets manager
- HTTP/queue/file boundaries: contracts, timeouts, retries, failure modes

## Checklist (blocking → nice)

### Blocking / must fix

- [ ] SQL injection possible (string-built queries)
- [ ] Missing transactions on multi-step writes
- [ ] Hardcoded credentials or secrets
- [ ] Critical path missing tests (money, auth, data integrity)
- [ ] Authorization / ownership checks missing on sensitive actions
- [ ] Unbounded queries or clear N+1

### High priority

- [ ] Input validation on external data
- [ ] Output escaped (XSS)
- [ ] Indexes / query performance reasonable
- [ ] Type / null safety (PHP 8+ types, Python hints)
- [ ] Error handling does not leak secrets
- [ ] Dependencies free of known vulns (when deps touched)

### Important

- [ ] Clear naming; single-responsibility
- [ ] Consistent with existing patterns
- [ ] Migrations included and safe
- [ ] Logging/observability adequate
- [ ] Resource cleanup (connections, files, locks)

### Nice / nits

- Style (PHPCS / Ruff / Black — automate)
- Minor comments
- Small pure-clarity refactors

## Example good feedback

- “This query is built with string concatenation — please switch to a prepared statement / parameterized query to eliminate SQL injection risk.”
- “This multi-table update should be wrapped in a transaction so we don’t leave partial state on failure.”
- “N+1 risk here: the loop will fire one query per user. Consider `with()` / `select_related` / `joinedload`.”

## Generic (any stack)

- Correctness vs stated intent
- Secrets / authz / injection on changed surfaces
- Tests for critical behaviour
- Destructive ops need dry-run / confirmation
- No live DB test targets
