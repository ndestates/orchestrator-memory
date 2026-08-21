# Bug Hunter Taxonomy

Use every category below unless the manifest/stack excludes it (e.g. no database → skip DB integrity).

## Severity

| Level | Meaning | Fix policy |
|-------|---------|------------|
| **critical** | Data loss, auth bypass, prod outage, secret exposure | Stop; suggest fix; never auto-fix without explicit approval |
| **high** | Wrong results, security weakness, race with user impact | Suggest fix; auto-fix only if trivial + tests prove safety |
| **medium** | Edge-case failure, missing validation, poor error handling | Fix or suggest with reproduction steps |
| **low** | Code smell, minor inconsistency, dead code | Suggest; auto-fix if isolated |
| **info** | Potential weakness, missing test, observability gap | Log as weakness; optional hardening |

## Categories (scan all applicable)

### 1. Logic & correctness
- Off-by-one, wrong operators, inverted conditions
- Unreachable branches, dead assignments
- Incorrect defaults, missing early returns
- State machine gaps (invalid transitions)
- Idempotency violations (double-submit, duplicate charges)

### 2. Null, types & boundaries
- Null/undefined dereference (PHP null-safe gaps, JS optional chaining)
- Empty array/string edge cases
- Integer overflow, float precision
- Enum/constant drift (string literals vs constants)

### 3. Concurrency & async
- Race conditions, TOCTOU
- Missing locks/transactions
- Promise/async unhandled rejection
- Queue job retries without idempotency

### 4. Error handling & resilience
- Swallowed exceptions (empty catch)
- Generic catch without rethrow/log
- Missing fallback when external service fails
- No timeout/retry on HTTP/DB calls

### 5. Data integrity
- Missing FK constraints, orphan rows
- Soft-delete leaks (queries missing `deleted_at`)
- Migration rollback gaps
- Model ↔ schema drift (hand off to model-schema-check)

### 6. Security surface (deep dive → security-audit-agent)
- SQL injection patterns, raw queries
- XSS in Blade/React/Vue output
- Mass assignment, missing authorization checks
- Debug endpoints, `APP_DEBUG` in prod config samples
- Secrets in repo (grep; full audit → security-audit-agent)

### 7. Configuration & environment
- `.env.example` missing keys used in code
- Wrong default env for prod
- Feature flags always on/off
- Hardcoded URLs, paths, credentials

### 8. Performance & resources
- N+1 queries (Eloquent `with()` missing)
- Unbounded loops/queries (no pagination)
- Memory leaks (unclosed streams, event listeners)
- Synchronous work in request path that should queue

### 9. API & integration contracts
- Request/response shape drift vs docs/cache
- Webhook signature verification missing
- Breaking changes without versioning
- Idempotent webhook handlers

### 10. Tests & observability
- Critical path without test
- Flaky test patterns (sleep, time-dependent)
- Missing logging on failure paths
- No metrics/alerts on error rates

### 11. Frontend & UX (when applicable)
- Form validation only client-side
- Stale state after mutation
- Accessibility blockers on critical flows

### 12. Infrastructure & deploy (hand off to project-drift-guardian)
- CI gaps, missing gates
- Container/config drift

## Weakness vs bug

- **Bug:** reproducible or provably wrong behaviour now.
- **Weakness:** design gap, missing guard, or latent failure under load/change.

Label weaknesses separately; do not inflate severity.

## Specialist handoffs

| Finding type | Delegate to |
|--------------|-------------|
| Auth, secrets, OWASP | security-audit-agent |
| Schema/migrations | schema-audit-agent, model-schema-check |
| Scope/TODO drift | project-drift-guardian |
| Test gaps / new tests | test-specialist-agent (after test-safety-agent) |
| Laravel/Filament specifics | laravel-expert-agent |
| MySQL tuning | mysql-database-expert |