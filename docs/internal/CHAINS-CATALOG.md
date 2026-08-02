# Chains catalog (internal)

> **INTERNAL — not for public release.** Full chain → step → skill/prompt invocation map.

**Count:** 63 chains in `chains/registry.yaml`.

## How chains run

1. User: `/chain <id>` or intent match (e.g. “session start”).
2. Agent loads chain skill (`.grok/skills/chain/`) + chain block from registry (MCP `get_chain_detail` preferred).
3. Phase 0: manifest + cache spine (`token_policy`).
4. Steps run in order; `required: true` must succeed; `when:` may skip optional steps.
5. Handoffs ≤80 tokens; completion via `chain-completion-write.sh`.

## Catalog

### `ai-maturity` — AI Engineering Maturity

Cache load → 8-stage maturity assessment

**Intents:** `ai maturity`, `engineering maturity`, `adoption stage`, `ai engineering`, `maturity assessment`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `assess` | skill | `ai-engineering-maturity` | True | — |

### `beta-ready` — Beta Ready Checklist

Cache load → beta checklist → drift gate

**Intents:** `beta ready`, `beta checklist`, `ready for beta`, `pre-beta`, `launch readiness`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `checklist` | prompt | `beta-ready-checklist` | True | — |
| `drift` | skill | `project-drift-guardian` | True | — |

### `bug-hunt` — Bug Hunt

Cache load → bug scan (report-only). For fixes use bug-hunt-fix or pass "fix" in args

**Intents:** `find bugs`, `hunt bugs`, `bug hunt`, `what could break`, `code review bugs`, `weakness scan`, `defect hunt`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |

### `bug-hunt-deep` — Bug Hunt Deep

Bug hunt (report) → security → schema → test safety → test gaps. Fix variant bug-hunt-fix-deep

**Intents:** `deep bug hunt`, `comprehensive bug review`, `full defect scan`, `bugs and security`, `hunt all issues`

token_tier=`high` · max_steps=`6` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `schema` | skill | `schema-audit-agent` | False | database_project |
| `safety` | skill | `test-safety-agent` | False | tests_requested |
| `tests` | skill | `test-specialist-agent` | False | test_gaps_found |

### `bug-hunt-fix` — Bug Hunt and Fix

Cache load → hunt → apply safe fixes → test safety → verify tests

**Intents:** `fix bugs`, `bug hunt fix`, `hunt and fix`, `repair bugs`, `patch defects`, `fix issues found`

token_tier=`high` · max_steps=`4` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | fixes_applied |
| `tests` | skill | `test-specialist-agent` | False | fixes_applied |

### `bug-hunt-fix-deep` — Bug Hunt Fix Deep

Deep hunt with fixes → security suggest → test safety → tests for regressions

**Intents:** `deep fix bugs`, `fix all bugs`, `comprehensive fix`, `hunt fix and test`

token_tier=`high` · max_steps=`6` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | fixes_applied |
| `tests` | skill | `test-specialist-agent` | True | fixes_applied |
| `schema` | skill | `schema-audit-agent` | False | database_project |

### `bug-hunt-pre-deploy` — Bug Hunt Pre-Deploy

Drift gate → bug hunt (report) → security → test safety. Fix variant append "fix" to args

**Intents:** `pre-deploy bugs`, `release bug check`, `ship readiness bugs`, `deploy bug scan`, `bugs before deploy`

token_tier=`high` · max_steps=`5` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | — |
| `schema` | prompt | `model-schema-check` | False | database_project |

### `bug-hunt-pre-deploy-fix` — Bug Hunt Pre-Deploy Fix

Drift → hunt with safe fixes → security → test safety → schema check

**Intents:** `pre-deploy fix`, `fix before deploy`, `ship with fixes`, `release bug fixes`

token_tier=`high` · max_steps=`6` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | fixes_applied |
| `tests` | skill | `test-specialist-agent` | False | fixes_applied |
| `schema` | prompt | `model-schema-check` | False | database_project |

### `cache-freshness-watch` — Cache Freshness Watch

L1 cache staleness report then verifier gate

**Intents:** `cache freshness`, `cache stale`, `cache watch`, `refresh cache`, `codebase scan stale`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `check` | skill | `cache-freshness-check` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `cache-rebuild` — Cache Rebuild

Cache load → full codebase scan and cache write

**Intents:** `refresh cache`, `rebuild cache`, `stale cache`, `read codebase`, `codebase scan`, `update cache`

token_tier=`high` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `scan` | skill | `acquire-codebase-knowledge` | True | — |

### `chain-health-watch` — Chain Health Watch

L1 chain registry audit report then verifier gate

**Intents:** `chain health`, `chain audit`, `registry audit`, `broken chain`, `chains registry`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `audit` | skill | `loop-engineering` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `ci-branch-readiness` — CI Branch Readiness

Cache → branch CI/CD analysis (per-wave) → GitHub policy → git guardrails; block push on BLOCKED

**Intents:** `ci readiness`, `will ci pass`, `check workflows before push`, `branch ci`, `actions readiness`, `pre-push ci`, `github ci cd`, `ci branch readiness`

token_tier=`medium` · max_steps=`4` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `readiness` | skill | `github-ci-readiness-expert` | True | — |
| `github` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |

### `code-review` — Code Review (diff-scoped)

Lean, token-efficient review of the working diff — correctness + obvious issues; security pass only when auth/secrets/permissions change. Report-only.

**Intents:** `code review`, `review code`, `review the diff`, `review my changes`, `review changes`, `pre-commit review`, `review before commit`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `review` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | False | auth_or_secrets_or_permissions_touched |

### `complex-task` — Complex Task Orchestration

Cache load then orchestrator decomposition for multi-domain work

**Intents:** `orchestrate`, `multi-step`, `complex`, `several agents`, `implement feature`

token_tier=`high` · max_steps=`2` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `plan` | prompt | `orchestrator-v2` | True | — |

### `cyber-essentials-hunt` — Cyber Essentials Bug Hunt

CE assess → bug hunt → security audit for code compliance gaps

**Intents:** `cyber essentials bugs`, `CE bug hunt`, `compliance bugs`, `CE weaknesses`, `hunt CE gaps`

token_tier=`high` · max_steps=`4` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `ce` | skill | `cyber-security-essentials` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |

### `cyber-essentials-maturity` — Cyber Essentials Maturity

CE assess → AI engineering maturity → security audit for SDLC posture

**Intents:** `cyber maturity`, `CE and AI maturity`, `engineering cyber compliance`, `SDLC cyber essentials`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `ce` | skill | `cyber-security-essentials` | True | — |
| `maturity` | skill | `ai-engineering-maturity` | True | — |
| `security` | skill | `security-audit-agent` | True | — |

### `cyber-essentials-pre-deploy` — Cyber Essentials Pre-Deploy

Drift gate → CE assess → pre-deploy bug hunt → security audit

**Intents:** `CE pre-deploy`, `cyber essentials deploy`, `CE ship check`, `certification before release`

token_tier=`high` · max_steps=`5` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `ce` | skill | `cyber-security-essentials` | True | — |
| `hunt` | skill | `bug-hunter-agent` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | — |

### `cyber-essentials-review` — Cyber Essentials Review

UK NCSC Cyber Essentials code/config assess → deep security audit

**Intents:** `cyber essentials`, `cyber essentials review`, `UK CE`, `NCSC compliance`, `certification readiness`, `supplier cyber assurance`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `ce` | skill | `cyber-security-essentials` | True | — |
| `security` | skill | `security-audit-agent` | True | — |

### `database-design` — Database Design

Data architect ER design → schema audit → engine expert (manifest-driven). Cache-first.

**Intents:** `database design`, `schema design`, `ER diagram`, `data model`, `mermaid er`, `normalise schema`, `improve database`, `greenfield database`, `laravel schema`, `eloquent model`

token_tier=`medium` · max_steps=`8` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `architect` | skill | `data-architect-expert` | True | — |
| `model_check` | prompt | `model-schema-check` | False | laravel_project |
| `audit` | skill | `schema-audit-agent` | False | existing_schema |
| `laravel` | skill | `laravel-expert-agent` | False | laravel_project |
| `mysql_impl` | skill | `mysql-database-expert` | False | mysql_engine |
| `mariadb_impl` | skill | `mariadb-database-expert` | False | mariadb_engine |
| `sqlite_impl` | skill | `sqlite-database-expert` | False | sqlite_engine |
| `filament` | skill | `filament-panel-review` | False | filament_project |

### `delivery` — Safe Delivery

Branch alignment → diff-scoped code review → git guardrails → tests when code changed

**Intents:** `commit`, `push`, `PR`, `deliver`, `merge`, `release`

token_tier=`medium` · max_steps=`5` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `branch` | skill | `branch-context-agent` | True | — |
| `review` | skill | `bug-hunter-agent` | False | code_changed |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `test-safety` | skill | `test-safety-agent` | False | code_changed |
| `tests` | skill | `test-specialist-agent` | False | code_changed |

### `deploy-check` — Deploy Check

Drift → hardened Docker → GitHub workflows → git guardrails → DO deploy → eval

**Intents:** `deploy`, `production`, `digitalocean`, `CI`, `release to prod`

token_tier=`high` · max_steps=`7` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `docker` | skill | `docker-expert` | True | — |
| `workflows` | skill | `github-workflow-expert` | True | — |
| `github` | skill | `github-expert` | False | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `deploy` | skill | `digitalocean-app-platform-docr-deploy` | True | — |
| `eval` | skill | `eval/maintenance-task` | False | — |

### `deploy-dns-infra` — Deploy DNS and Perimeter

Route 53 app + email DNS (DKIM) → DO firewall → SES verify → git commit DNS JSON

**Intents:** `deploy dns`, `production dns`, `dkim deploy`, `firewall setup`, `route53 deploy`, `app subdomain`, `email dns go live`

token_tier=`high` · max_steps=`6` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `dns` | skill | `aws-route53-dns` | True | — |
| `firewall` | skill | `digitalocean-app-platform-docr-deploy` | True | — |
| `ses` | skill | `amazon-ses-email` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `eval` | skill | `eval/maintenance-task` | False | — |

### `didit-identity-setup` — Didit Identity Setup

Drift gate → Didit KYC/KYB integration

**Intents:** `didit`, `kyc`, `kyb`, `aml`, `identity verification`, `biometric verification`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `didit` | skill | `didit-identity-integration` | True | — |

### `docker-deploy` — Docker Deploy Setup

Hardened image → CI workflow → GitHub policy → git guardrails → DO registry

**Intents:** `docker deploy`, `hardened dockerfile`, `thin production image`, `dockerignore`, `DOCR build`, `container CI`

token_tier=`high` · max_steps=`6` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `docker` | skill | `docker-expert` | True | — |
| `workflows` | skill | `github-workflow-expert` | True | — |
| `github` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `deploy` | skill | `digitalocean-app-platform-docr-deploy` | False | deploy_requested |

### `documentation-full` — Full Documentation

Cache load → codebase scan (optional) → README → GitHub Docs-style site + cache

**Intents:** `full documentation`, `document project`, `write docs`, `onboarding docs`, `documentation specialist`, `api docs`, `architecture docs`

token_tier=`high` · max_steps=`4` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `scan` | skill | `acquire-codebase-knowledge` | False | — |
| `readme` | skill | `readme-specialist` | True | — |
| `docs` | skill | `documentation-specialist` | True | — |

### `documentation-refresh` — Documentation Refresh

Cache load → README polish → doc set update (no full scan)

**Intents:** `refresh docs`, `update documentation`, `doc refresh`, `sync docs to cache`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `readme` | skill | `readme-specialist` | True | — |
| `docs` | skill | `documentation-specialist` | True | — |

### `eod-shutdown` — End of Day Shutdown

Close TODO → README → token report → ddev-cleanup (mandatory clean git) → emit useful daily learnings to vault graph (self-learning brain) if activity detected. All changes committed, porcelain empty, brain updated.

**Intents:** `end of day`, `shutdown`, `ddev cleanup`, `stop work`, `daily cleanup`, `mark work done`, `close todo`, `eod`, `eod session`, `eod-session`, `eod shutdown`, `clean git`

token_tier=`low` · max_steps=`6` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `todo` | skill | `todo-specialist-agent` | True | — |
| `changelog` | skill | `changelog-specialist` | False | — |
| `readme` | skill | `readme-specialist` | True | — |
| `tokens` | skill | `token-usage-meter` | False | — |
| `cleanup` | skill | `ddev-cleanup` | True | — |
| `wiki-fileback` | skill | `llm-wiki` | False | wiki_mode_lean_or_full |
| `vault-emit` | skill | `ddev-cleanup` | False | — |

### `filament-review` — Filament Panel Review

Cache load → panel audit → security follow-up

**Intents:** `filament review`, `panel review`, `filament panel`, `admin panel audit`, `resource review`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `panels` | skill | `filament-panel-review` | True | — |
| `security` | skill | `security-audit-agent` | False | auth_or_permissions_touched |

### `frontend-ui` — Frontend UI and Components

HTML/Tailwind ui_spec → stack expert (Laravel/Livewire/HTMX/Go default; SPA only when manifest matches)

**Intents:** `frontend ui`, `dashboard ui`, `form design`, `blade ui`, `livewire ui`, `htmx ui`, `filament ui`, `tailwind components`, `server rendered ui`, `design tokens`, `ui spec`, `accessibility ui`

token_tier=`medium` · max_steps=`7` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `frontend` | skill | `frontend-web-design-expert` | True | — |
| `laravel` | skill | `laravel-expert-agent` | False | laravel_project |
| `go` | skill | `go-expert` | False | go_framework |
| `nextjs` | skill | `nextjs-expert` | False | nextjs_framework |
| `astro` | skill | `astro-expert` | False | astro_framework |
| `nuxt` | skill | `nuxt-expert` | False | nuxt_framework |

### `github-ci-watch` — GitHub CI Watch

L1 GitHub Actions health report then verifier gate

**Intents:** `github ci watch`, `workflow health`, `failed workflow runs`, `actions audit`, `ci watch`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `ci` | skill | `github-workflow-expert` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `github-workflow-setup` — GitHub Workflow Setup

Cache → CI policy review → workflow/secrets CRUD → security audit → git delivery

**Intents:** `github workflow`, `create workflow`, `add workflow`, `amend workflow`, `delete workflow`, `set secrets`, `gh secret`, `github actions setup`, `CI workflow`, `deploy workflow`, `workflow automation`, `github-workflow-expert`

token_tier=`medium` · max_steps=`5` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `policy` | skill | `github-expert` | True | — |
| `workflows` | skill | `github-workflow-expert` | True | — |
| `security` | skill | `security-audit-agent` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |

### `laravel-database-design` — Laravel Database Design

Full stack DB design — architect → model check → Laravel → engine → Filament. Cache-first.

**Intents:** `laravel database`, `filament schema`, `eloquent design`, `model migration`, `database with filament`, `laravel ER diagram`

token_tier=`high` · max_steps=`8` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `architect` | skill | `data-architect-expert` | True | — |
| `model_check` | prompt | `model-schema-check` | True | — |
| `audit` | skill | `schema-audit-agent` | False | existing_schema |
| `laravel` | skill | `laravel-expert-agent` | True | — |
| `mysql_impl` | skill | `mysql-database-expert` | False | mysql_engine |
| `mariadb_impl` | skill | `mariadb-database-expert` | False | mariadb_engine |
| `sqlite_impl` | skill | `sqlite-database-expert` | False | sqlite_engine |
| `filament` | skill | `filament-panel-review` | False | filament_project |

### `laravel-feature` — Laravel Feature

Branch alignment → Laravel expert → test safety and tests when code changes

**Intents:** `laravel`, `filament`, `eloquent`, `livewire`, `artisan`, `implement laravel`

token_tier=`medium` · max_steps=`5` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `branch` | skill | `branch-context-agent` | True | — |
| `laravel` | skill | `laravel-expert-agent` | True | — |
| `safety` | skill | `test-safety-agent` | False | code_changed |
| `tests` | skill | `test-specialist-agent` | False | code_changed |

### `loop-daily` — Loop Daily Triage

L1 triage report then verifier gate

**Intents:** `loop triage`, `daily triage`, `loop report`, `STATE.md`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `triage` | skill | `loop-triage` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `loop-engineering-audit` — Loop Engineering Audit

Cache load → loop maturity and readiness assessment

**Intents:** `loop engineering`, `loop maturity`, `loop audit`, `loop readiness`, `loop patterns`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `audit` | skill | `loop-engineering` | True | — |

### `loqate-address-setup` — Loqate Address Setup

Drift gate → Loqate Address Capture integration

**Intents:** `loqate`, `address capture`, `address validation`, `postcode lookup`, `type-ahead address`

token_tier=`medium` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `loqate` | skill | `loqate-address-integration` | True | — |

### `migration-safe` — Migration Safe

Schema check → audit → test safety → engine → Laravel models (when laravel)

**Intents:** `migration`, `schema`, `database change`, `alter table`, `model drift`

token_tier=`medium` · max_steps=`7` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `check` | prompt | `model-schema-check` | True | — |
| `audit` | skill | `schema-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | — |
| `mysql` | skill | `mysql-database-expert` | False | mysql_engine |
| `mariadb` | skill | `mariadb-database-expert` | False | mariadb_engine |
| `sqlite` | skill | `sqlite-database-expert` | False | sqlite_engine |
| `laravel` | skill | `laravel-expert-agent` | False | laravel_project |
| `filament` | skill | `filament-panel-review` | False | filament_project |

### `paypal-setup` — PayPal Billing Setup

Drift gate → PayPal integration configuration

**Intents:** `paypal`, `billing setup`, `checkout`, `webhook`, `invoice`, `subscription billing`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `paypal` | skill | `paypal-billing-integration` | True | — |

### `pre-flight` — Pre-Flight Check

Branch scope → drift scan → test DB safety before starting work

**Intents:** `pre flight`, `before starting`, `start feature`, `scope check`, `am I on track`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `branch` | skill | `branch-context-agent` | True | — |
| `drift` | skill | `project-drift-guardian` | True | — |
| `safety` | skill | `test-safety-agent` | False | tests_planned |

### `prod-db-ops` — Production DB Operations

Drift gate → prod DB maintenance → post-maintenance eval

**Intents:** `production database`, `prod db`, `db import`, `database maintenance`, `clean prod`, `listings refresh`

token_tier=`high` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `drift` | skill | `project-drift-guardian` | True | — |
| `maintain` | skill | `prod-db-maintenance` | True | — |
| `eval` | skill | `eval/maintenance-task` | True | — |

### `promote-master` — Promote Master

Audit develop → sync master conflicts → merge develop to master via PR

**Intents:** `promote master`, `develop to master`, `merge develop into master`, `master promotion`, `promote to production`, `merge develop`

token_tier=`medium` · max_steps=`4` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `branch` | skill | `branch-context-agent` | True | — |
| `gates` | skill | `git-workflow-guardrails` | True | — |
| `github` | skill | `github-expert` | True | — |
| `promote` | skill | `git-workflow-guardrails` | True | — |

### `push-secrets-guard` — Push Secrets Guard

GitHub posture review → git guardrails with mandatory secrets/env pre-push hooks (GitGuardian-safe)

**Intents:** `push secrets`, `gitguardian`, `pre-push guard`, `env files push`, `secrets guard`, `no secrets push`, `github expert guardrails`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `github` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |

### `qa-gate` — QA Gate (after complex work)

After bug-hunt / rotation / analysis → qa-agent gate for sign-off

**Intents:** `qa gate`, `quality signoff`, `qa after task`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `qa` | skill | `qa-agent` | True | — |

### `qa-pre-deploy` — QA Pre-Deploy

Full qa-agent pre-deploy (risks, tests, domain, readiness)

**Intents:** `pre deploy qa`, `qa before release`, `ship readiness qa`

token_tier=`high` · max_steps=`5` · max_cache_files=`4`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `drift` | skill | `project-drift-guardian` | True | — |
| `qa` | skill | `qa-agent` | True | — |
| `safety` | skill | `test-safety-agent` | True | — |
| `tests` | skill | `test-specialist-agent` | False | — |

### `qa-pre-pr` — QA Pre-PR Gate

Cache → qa-agent pre-pr (diff focus, safety, domain risks, tests). Pass specialization (e.g. facebook-stats, e-ndsign) via skill_args or invocation.

**Intents:** `pre pr qa`, `qa before pr`, `quality gate pre merge`

token_tier=`medium` · max_steps=`4` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `branch` | skill | `branch-context-agent` | False | — |
| `qa` | skill | `qa-agent` | True | — |
| `safety` | skill | `test-safety-agent` | False | — |

### `qa-scan` — QA Scan

Cache load → qa-agent scan (report + checklist). Lightweight health check.

**Intents:** `qa scan`, `quality check`, `run qa`, `qa review`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `qa` | skill | `qa-agent` | True | — |

### `repo-health` — Repo Health Check

GitHub audit → git workflow verification → drift and sync gates

**Intents:** `repo health`, `all in order`, `pull branches`, `sync branches`, `fetch all branches`, `github audit`, `drift check`, `make sure all in order`, `branch hygiene`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `github` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `drift` | skill | `project-drift-guardian` | True | — |

### `repo-health-watch` — Repo Health Watch

L1 branch/PR hygiene report then verifier gate

**Intents:** `repo health watch`, `branch hygiene watch`, `weekly repo health`, `stale branches`, `branch divergence`

token_tier=`low` · max_steps=`3` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `github` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `research-deep-dive` — Research Deep Dive (external)

Cache load → perspective frame → gather (user-approved sources) → research memo

**Intents:** `research before implement`, `deep dive`, `domain research`, `integration research`, `compliance research`, `architecture options`, `unfamiliar domain`

token_tier=`medium` · max_steps=`4` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `frame` | skill | `research-deep-dive` | True | — |
| `gather` | skill | `research-deep-dive` | True | — |
| `memo` | skill | `research-deep-dive` | True | — |

### `security-review` — Security Review

Security audit with test DB safety gate

**Intents:** `security`, `auth`, `permissions`, `consent`, `secrets`, `CDD`

token_tier=`medium` · max_steps=`2` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `audit` | skill | `security-audit-agent` | True | — |
| `safety` | skill | `test-safety-agent` | False | tests_requested |

### `ses-email-setup` — SES Email Setup

Route 53 email DNS (DKIM/SPF/DMARC) then Amazon SES — use deploy-dns-infra for go-live

**Intents:** `ses`, `email setup`, `DKIM`, `SPF`, `DMARC`, `inbound email`

token_tier=`medium` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `dns` | skill | `aws-route53-dns` | True | — |
| `ses` | skill | `amazon-ses-email` | True | — |

### `session-end` — Session End (mid-day pause)

Pause work to leave and return later the same day. Captures WIP checkpoint, optional TODO resume note, workspace pointer + light vault pause lesson. Does NOT require clean git, does NOT stop ddev, does NOT run full eod-shutdown.

**Intents:** `session end`, `session-end`, `end session`, `pause session`, `pause work`, `break`, `back later`, `mid day`, `midday`, `leave for now`, `step away`

token_tier=`low` · max_steps=`4` · max_cache_files=`1`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `checkpoint` | skill | `cache-efficient` | True | — |
| `changelog` | skill | `changelog-specialist` | False | — |
| `meter` | skill | `token-usage-meter` | False | — |
| `handoff` | skill | `cache-efficient` | True | — |

### `session-start` — Session Start

Resume-first gate → standup (runtime + resume-branch) → security sweep → lean cache load (0 files when card fresh) → compound gate → working mode

**Intents:** `session start`, `session-start`, `start session`, `daily`, `standup`, `morning`, `what should I work on`

token_tier=`low` · max_steps=`9` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `resume-first` | skill | `session-resume` | True | — |
| `standup` | skill | `daily-standup-with-cache` | True | — |
| `security-hygiene` | skill | `cyber-security-essentials` | True | — |
| `load` | prompt | `load-project-cache-first` | True | — |
| `wiki-brief` | skill | `llm-wiki` | False | wiki_mode_lean_or_full |
| `compound-gate` | skill | `app-compound-gate` | False | loop_enabled_app |
| `changelog-init` | skill | `changelog-specialist` | False | token_context_ok_or_unreleased |
| `meter` | skill | `token-usage-meter` | False | — |
| `tone` | skill | `cache-efficient` | False | — |

### `template-deploy` — Template Deploy

Cache load then deploy .grok + root chains to target project

**Intents:** `deploy template`, `deploy grok`, `deploy to project`, `push orchestrator to`, `template deploy`, `update fork from orchestrator`

token_tier=`medium` · max_steps=`3` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `deploy` | skill | `orchestrator-deploy` | True | — |
| `decontaminate` | skill | `template-decontaminate` | True | — |

### `token-monitor` — Token Monitor

Sync Grok session context size, log trends, warn on bloat and cache misses

**Intents:** `token usage`, `token meter`, `token monitor`, `cache efficiency`, `monitor tokens`, `how many tokens`

token_tier=`low` · max_steps=`1` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `meter` | skill | `token-usage-meter` | True | — |

### `vector-db-assess` — Vector DB Fit Assessment

Assess whether project benefits from vector DB — report-only recommendation. Cache-first.

**Intents:** `need vector database`, `vector db assessment`, `should we use embeddings`, `rag feasibility`, `semantic search fit`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `assess` | skill | `vector-database-expert` | True | — |

### `vector-db-setup` — Vector DB Setup

Vector store selection, RAG schema, hybrid search — cache-first; optional ER via data-architect

**Intents:** `vector database`, `embeddings`, `rag schema`, `pgvector`, `qdrant`, `pinecone`, `semantic search`, `hybrid search`

token_tier=`medium` · max_steps=`6` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `assess` | skill | `vector-database-expert` | True | — |
| `architect` | skill | `data-architect-expert` | False | vector_recommended |
| `vector` | skill | `vector-database-expert` | False | vector_recommended |
| `security` | skill | `security-audit-agent` | False | pii_in_embeddings |
| `laravel` | skill | `laravel-expert-agent` | False | laravel_project |
| `engine` | skill | `mysql-database-expert` | False | mysql_engine |

### `web-design` — Web Build and Design

Design lead → frontend UI spec → stack expert (Laravel/Go default; SPA when manifest matches) → README

**Intents:** `marketing page`, `landing page`, `pricing page`, `web design`, `saas landing`, `public site`, `blade marketing`, `laravel landing`, `static site`

token_tier=`medium` · max_steps=`8` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `design` | skill | `web-build-design` | True | — |
| `frontend` | skill | `frontend-web-design-expert` | True | — |
| `laravel` | skill | `laravel-expert-agent` | False | laravel_project |
| `go` | skill | `go-expert` | False | go_framework |
| `nextjs` | skill | `nextjs-expert` | False | nextjs_framework |
| `astro` | skill | `astro-expert` | False | astro_framework |
| `nuxt` | skill | `nuxt-expert` | False | nuxt_framework |
| `readme` | skill | `readme-specialist` | False | — |

### `wiki-ingest` — Wiki Ingest

Ingest one raw source into the LLM wiki (propose multi-page updates, index + log). L1 approval for writes; dual-write vault when accepted.

**Intents:** `wiki ingest`, `ingest wiki`, `llm wiki ingest`, `karpathy ingest`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `ingest` | skill | `llm-wiki` | True | — |

### `wiki-lint` — Wiki Lint

L1 health check of the LLM wiki (contradictions, orphans, stale sources). Report-only; no auto-fix.

**Intents:** `wiki lint`, `lint wiki`, `wiki health`, `llm wiki lint`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `lint` | skill | `llm-wiki` | True | — |

### `wiki-lint-watch` — Wiki Lint Watch

L1 wiki health (wiki_lint_check + host snapshot) then loop-verifier. Report-only; manual until scheduled.

**Intents:** `wiki lint watch`, `wiki-lint-watch`, `weekly wiki lint`

token_tier=`low` · max_steps=`3` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `host` | skill | `llm-wiki` | True | — |
| `verify` | skill | `loop-verifier` | True | — |

### `wiki-query` — Wiki Query

Answer a question from the wiki (index-first, capped pages). Optional file-back.

**Intents:** `wiki query`, `ask wiki`, `llm wiki query`, `query knowledge wiki`

token_tier=`low` · max_steps=`2` · max_cache_files=`2`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `query` | skill | `llm-wiki` | True | — |

### `workflow-debug` — Workflow Debug / Failure Diagnosis

Cache load → github-workflow-expert (diagnose-failure.sh + log analysis) → github-expert (policy) → git-workflow-guardrails (apply fix + commit). Stops continual CI failures with root-cause + exact remediation.

**Intents:** `workflow debug`, `debug workflow`, `why ci failing`, `diagnose failure`, `fix workflow failure`, `workflow error`, `github action debug`, `ci failure`, `debug github workflow`, `workflow not working`

token_tier=`medium` · max_steps=`4` · max_cache_files=`3`

| Step | Type | Invoke | Required | When |
|------|------|--------|----------|------|
| `load` | prompt | `load-project-cache-first` | True | — |
| `diagnose` | skill | `github-workflow-expert` | True | — |
| `policy` | skill | `github-expert` | True | — |
| `git` | skill | `git-workflow-guardrails` | True | — |
