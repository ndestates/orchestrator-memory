# Slash commands catalog

[UPDATED by scripts/register-all-slash-commands.py]

Every skill under `.grok/skills/` is registered for **Grok**, **Claude**, **Copilot**, and **Cursor**.

## Canonical session opener

```text
/chain session-start
```

Type that on the **Grok** or **Claude** command line (chain skill / command).

## Skills (slash)

| Slash | Description |
|-------|-------------|
| `/acquire-codebase-knowledge` | Map, document, and onboard into any project codebase. |
| `/ai-content-guardrails` | Defense in depth for prompt injection, PII leakage, and toxic content. |
| `/ai-engineering-maturity` | Framework for the 8 stages of AI engineering maturity (team and organization view). |
| `/always-on-memory` | Always-on memory agent: ingest/consolidate/query via project model-route catalog + all agents; SQLite store; inbox watch; session brief. |
| `/amazon-ses-email` | Full skill for setting up Amazon SES email for the project domain (sending + receiving). |
| `/app-compound-gate` | Per-app compound learning gate for session-start: assess local loop spine (STATE, VISION, lessons-state), load durable lessons when READY, close SCAFFOLD or unc |
| `/astro-expert` | Astro 4/5 expert: content collections, islands architecture, View Transitions, MDX, static/SSR/hybrid output, Tailwind integration. Cache-first. Use on /astro-e |
| `/aws-route53-dns` | AWS Route 53 expert: hosted zones, production app DNS (A/CNAME/ALIAS), deploy-time DKIM/SPF/DMARC/MX for SES, nameserver delegation, DNS-as-code change batches. |
| `/branch-context` | Branch scope and TODO-alignment analyzer for project. Summarize branch purpose, changes vs active TODO, detect drift before merge or major work. Use when user r |
| `/bug-hunter` | Specialist bug and weakness hunter for any codebase: logic errors, edge cases, error handling, races, data integrity, config bugs, performance, integration gaps |
| `/cache-efficient` | project cache-first session with minimal tokens: load INDEX + targeted cache/memories only, respond in short bullets. |
| `/cache-freshness-check` | Check docs/codebase cache freshness against manifest cache_stale_days, .codebase-scan.txt, README [UPDATED] markers, git branch, and TODO branch. |
| `/chain` | Run a named chain. Default session opener: /chain session-start |
| `/changelog-specialist` | Incremental changelog for project: session log after every substantive action, consolidate into CHANGELOG.md [Unreleased] at EOD, generate PR body. |
| `/code-review` | Diff-scoped code review quality gate. Wires the existing strict maintainability code-review skill (code judo / file-size / spaghetti bar) together with process, |
| `/cyber-security-essentials` | UK NCSC Cyber Essentials compliance assessor for code, config, and CI. |
| `/daily-standup` | Alias for /daily-standup-with-cache. Start a daily session: fetch remote branches, report latest remote branch worked on, then cache + TODO + briefing. |
| `/daily-standup-with-cache` | Start a daily working session on project using the local cache + today's TODO + open concerns. This is the recommended prompt/skill for almost every normal deve |
| `/data-architect-expert` | Senior data architect: greenfield ER design, schema analysis and improvement, normalisation, indexing strategy, migration roadmaps. |
| `/ddev-cleanup` | End-of-day cleanup for Grok Build + ddev projects. |
| `/ddev-local-runtime` | Mandatory rule that all local project commands for the project repository run inside the DDEV runtime, not on the host shell. |
| `/didit-identity-integration` | Full skill for Didit identity verification (KYC, KYB, AML, biometrics) in Laravel app repos. |
| `/digitalocean-deploy` | Senior DigitalOcean DevOps expert for project hosting (App Platform + DOCR and/or Droplets), CI/CD via GitHub Actions, safe database updates, and no-drift deplo |
| `/docker-expert` | Docker expert for local dev and production deploy: multi-stage hardened images, minimal runtime layers, .dockerignore discipline, non-root users. |
| `/documentation-specialist` | Full-project documentation maker for orchestrator template or any forked app repo. |
| `/docx` | Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). |
| `/eval-maintenance-task` | Post-maintenance evaluation skill for production readiness tasks (registry cleanup, DB imports, live listings freshness, etc.). |
| `/filament-panel-review` | Review one or more of the 7 Filament 5 panels in project multi-panel architecture using the local cache first. |
| `/frontend-web-design-expert` | Framework-agnostic UI/UX expert: HTML, Tailwind, design tokens, responsive layouts, and WCAG AA a11y. |
| `/git-workflow-guardrails` | Git and githooks workflow for safe delivery. |
| `/github-ci-readiness-expert` | GitHub CI/CD branch readiness expert for wave projects. |
| `/github-expert` | GitHub platform expert for project workflows, Actions, PRs, security scanning, automation. |
| `/github-workflow-expert` | Programmatic GitHub Actions expert: create, amend, delete workflows in .github/workflows/, manage repo and environment secrets via gh CLI, dispatch and enable/d |
| `/go-expert` | Go 1.22+ expert: stdlib HTTP, chi/gin/echo (project-existing), sqlc/GORM, modules, testing, observability, Docker. |
| `/jersey-aml-compliance-expert` | Expert on Jersey anti-money laundering, counter-terrorist financing and counter-proliferation financing (AML/CFT/CPF). |
| `/jersey-data-protection-expert` | Expert on the Data Protection (Jersey) Law 2018 (DPJL) and the Data Protection Authority (Jersey) Law 2018. |
| `/laravel-expert` | Laravel 12 + Filament 5 expert for project. Use for architecture, resources, Eloquent, panels, services, Artisan, testing, or when /laravel-expert-agent. |
| `/llm-wiki` | Karpathy-style LLM wiki: ingest raw sources into a persistent markdown wiki, query with index-first navigation, lint for contradictions/orphans/stale pages. |
| `/load-project-cache-first` | Load project project cache (docs/codebase/ + TODO + CONCERNS + .grok/.copilot memories) first before any deep exploration. |
| `/loop-compound` | Compound learning closure (14-step roadmap steps 10–14): capture loop lessons, promote to STATE.md + secure hash-chained vault graph (reports/vault/events.jsonl |
| `/loop-engineering` | Loop engineering for this template: design systems that prompt agents, not hand prompts. |
| `/loop-triage` | L1 daily loop triage for the orchestrator template. |
| `/loop-verifier` | Independent verifier for loop outputs. Checks artifacts and rubric only — not maker reasoning. Enforces cache citations, L1 no-auto-fix, and loop-budget complia |
| `/loqate-address-integration` | Full skill for Loqate (GBG) Address Capture in Laravel app repos. |
| `/mariadb-database-expert` | MariaDB 10.x/11.x expert for project: InnoDB/Aria, Galera, replication, JSON, spatial, Laravel Eloquent, Python connectors. |
| `/model-route` | Suggest free open-source LLMs (Ollama) when the task does not need the current frontier model; offer stay \| oss \| install-oss \| free-cloud. Never silent-switch. |
| `/model-schema-check` | Review model vs database schema consistency on project using the local cache and project tooling. Use before/after migrations or when schema drift is suspected. |
| `/multi-workstream` | Multi-workstream session v2 + agent graphs. Operator UX is slash commands (/multi-workstream …). Same implementation on every host. Not multi-session SDK. |
| `/mysql-concurrency-test` | Design MySQL concurrency tests adapted for Laravel 12 + Eloquent (lockForUpdate, DB::transaction, queues, optimistic/pessimistic locking). |
| `/mysql-database-expert` | MySQL 8.x expert for project: InnoDB, JSON, window functions, CTEs, replication, Laravel Eloquent, Python connectors. |
| `/nextjs-expert` | Next.js 14/15 App Router expert: RSC, server actions, route handlers, middleware, Tailwind, auth patterns, Vercel/Node deploy. Cache-first. Use on /nextjs-exper |
| `/nuxt-expert` | Nuxt 3/4 expert: file-based routing, server routes, composables, Pinia, Nitro, SSR/SSG/prerender, Tailwind module. Cache-first. Use on /nuxt-expert or /chain we |
| `/orchestrator-deploy` | Deploy orchestrator .grok skills, prompts, agents, and root chains (CHAIN.md, chains/registry.yaml) to any target project. |
| `/paypal-billing` | Full skill for PayPal integration in project for payments and generating billing documents (invoices, receipts) directly at PayPal. |
| `/prod-db-maintenance` | Skill for invoking import or update of the production database as Stage 6 infrastructure (operating system). |
| `/project-drift-guardian` | Specialized guardian against project drift for project. |
| `/prompt-patterns` | High-signal prompt engineering patterns (grounded RAG with refusal, Socratic code review, strict formatting, complex structure). |
| `/qa-agent` | Full QA agent (reusable general structure + per-wave-project specializations). |
| `/read-codebase` | Backward-compatible alias for acquire-codebase-knowledge. |
| `/readme-specialist` | Documentation specialist for project README, guides, reference/*.md . Limited to docs only. Use on /readme-specialist or when improving project docs. |
| `/research-deep-dive` | Optional external-topic research before implementation. |
| `/schema-audit` | Read-only schema/migration auditor for project. Use on /schema-audit-agent or for drift analysis. |
| `/script-not-shell` | Avoid inline shell escaping failures by writing script files first. |
| `/security-audit` | Security, auth, permissions, CDD/consent auditor for project. Use on /security-audit-agent , post-dep or form changes. |
| `/session-context-envelope` | Fixed-size session spin-up for any platform. |
| `/session-resume` | Resume-first gate for session-start: when a fresh resume card exists, trust it for branch/done/open/cache and skip redundant TODO/STATE/git reads to save tokens |
| `/skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance with quantitative evals, parallel subagent runs (with/without or old/new ba |
| `/sqlite-database-expert` | SQLite expert for project: embedded DB, Laravel :memory:/file drivers, Python sqlite3, WAL mode, migrations, FTS5, strict tables. |
| `/template-decontaminate` | Post-deploy, pre-commit gate for forked app repos. |
| `/test-safety` | Enforce test DB safety and pre/post risk assessment for project tests. Use before running tests or on /test-safety-agent. |
| `/test-specialist` | Write/improve/convert tests (Pest preferred) for project. Preserves logic; follows safety. Use on /test-specialist-agent or test tasks. |
| `/todo-specialist` | Maintain project TODO-*.md (carry forward, prioritize, update from work). Use on /todo-specialist-agent or when syncing tasks. |
| `/token-usage-meter` | Always-on xAI/Grok token usage and prompt-cache monitor. |
| `/top-class-website-designer` | PhD-level full-stack website/web-app architect (Python backends + MySQL 8+). |
| `/vector-database-expert` | Vector database expert: fit assessment (should this project use vectors?), then pgvector, Qdrant, Pinecone, Weaviate, Chroma, RAG schema, hybrid search. |
| `/web-build-design` | Web build & design lead: conversion-focused SaaS marketing, pricing, portals. |
| `/web-cache-expert` | Website performance cache architect: HTTP/CDN, image and document caching, cache refresh/invalidation, and multi-layer cache architecture for Laravel and any we |
| `/webapp-testing` | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing br |
| `/webmcp-beta` | Beta WebMCP (browser page tools via navigator.modelContext). |

## Chains

Invoke via **`/chain <id>`** (same on Grok · Claude · Cursor `/chain`).

| Slash | Name |
|-------|------|
| `/chain ai-maturity` | AI Engineering Maturity |
| `/chain always-on-memory` | Always-On Memory |
| `/chain beta-ready` | Beta Ready Checklist |
| `/chain bug-hunt` | Bug Hunt |
| `/chain bug-hunt-deep` | Bug Hunt Deep |
| `/chain bug-hunt-fix` | Bug Hunt and Fix |
| `/chain bug-hunt-fix-deep` | Bug Hunt Fix Deep |
| `/chain bug-hunt-pre-deploy` | Bug Hunt Pre-Deploy |
| `/chain bug-hunt-pre-deploy-fix` | Bug Hunt Pre-Deploy Fix |
| `/chain cache-freshness-watch` | Cache Freshness Watch |
| `/chain cache-rebuild` | Cache Rebuild |
| `/chain chain-health-watch` | Chain Health Watch |
| `/chain ci-branch-readiness` | CI Branch Readiness |
| `/chain code-review` | Code Review (diff-scoped) |
| `/chain complex-task` | Complex Task Orchestration |
| `/chain cyber-essentials-hunt` | Cyber Essentials Bug Hunt |
| `/chain cyber-essentials-maturity` | Cyber Essentials Maturity |
| `/chain cyber-essentials-pre-deploy` | Cyber Essentials Pre-Deploy |
| `/chain cyber-essentials-review` | Cyber Essentials Review |
| `/chain database-design` | Database Design |
| `/chain delivery` | Safe Delivery |
| `/chain deploy-check` | Deploy Check |
| `/chain deploy-dns-infra` | Deploy DNS and Perimeter |
| `/chain didit-identity-setup` | Didit Identity Setup |
| `/chain docker-deploy` | Docker Deploy Setup |
| `/chain documentation-full` | Full Documentation |
| `/chain documentation-refresh` | Documentation Refresh |
| `/chain eod-shutdown` | End of Day Shutdown |
| `/chain filament-review` | Filament Panel Review |
| `/chain frontend-ui` | Frontend UI and Components |
| `/chain github-ci-watch` | GitHub CI Watch |
| `/chain github-workflow-setup` | GitHub Workflow Setup |
| `/chain laravel-database-design` | Laravel Database Design |
| `/chain laravel-feature` | Laravel Feature |
| `/chain loop-daily` | Loop Daily Triage |
| `/chain loop-engineering-audit` | Loop Engineering Audit |
| `/chain loqate-address-setup` | Loqate Address Setup |
| `/chain migration-safe` | Migration Safe |
| `/chain multi-workstream` | Multi-workstream |
| `/chain multi-workstream-demo` | Multi-workstream diamond demo |
| `/chain multi-workstream-diamond` | Multi-workstream diamond (Shape B recommend) |
| `/chain paypal-setup` | PayPal Billing Setup |
| `/chain pre-flight` | Pre-Flight Check |
| `/chain prod-db-ops` | Production DB Operations |
| `/chain promote-master` | Promote Master |
| `/chain push-secrets-guard` | Push Secrets Guard |
| `/chain qa-gate` | QA Gate (after complex work) |
| `/chain qa-pre-deploy` | QA Pre-Deploy |
| `/chain qa-pre-pr` | QA Pre-PR Gate |
| `/chain qa-scan` | QA Scan |
| `/chain repo-health` | Repo Health Check |
| `/chain repo-health-watch` | Repo Health Watch |
| `/chain research-deep-dive` | Research Deep Dive (external) |
| `/chain security-flywheel` | Security Flywheel |
| `/chain security-review` | Security Review |
| `/chain ses-email-setup` | SES Email Setup |
| `/chain session-end` | Session End (mid-day pause) |
| `/chain session-start` | Session Start |
| `/chain template-deploy` | Template Deploy |
| `/chain token-monitor` | Token Monitor |
| `/chain vector-db-assess` | Vector DB Fit Assessment |
| `/chain vector-db-setup` | Vector DB Setup |
| `/chain web-cache-review` | Web Cache Review |
| `/chain web-design` | Web Build and Design |
| `/chain webmcp-setup` | WebMCP Beta Setup |
| `/chain wiki-ingest` | Wiki Ingest |
| `/chain wiki-lint` | Wiki Lint |
| `/chain wiki-lint-watch` | Wiki Lint Watch |
| `/chain wiki-query` | Wiki Query |
| `/chain workflow-debug` | Workflow Debug / Failure Diagnosis |
| `/chain workstream-graph-demo` | Workstream graph example |

## Surfaces

| Host | How slashes appear |
|------|-------------------|
| Grok | `.grok/skills/*/SKILL.md` with `user-invocable: true` → `/name` |
| Claude Code | `.claude/commands/<name>.md` → `/name` |
| Cursor | `.cursor/commands/<name>.md` → `/name` in chat |
| Copilot | `.github/skills/` + `.copilot/skills/` |
| Gemini / ChatGPT | This catalog under `.gemini/prompts/` / `.chatgpt/prompts/` |

Re-run: `python3 scripts/register-all-slash-commands.py`
