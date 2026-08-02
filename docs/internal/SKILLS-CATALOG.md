# Skills catalog (internal)

> **INTERNAL — not for public release.** Generated inventory of `.grok/skills/` with why/when and invocation.

**Count:** 72 skill packages under `.grok/skills/`.

## How skills are invoked

| Path | How |
|------|-----|
| Slash / skill name | Grok: `/skill-name` or skill menu |
| Claude | `.claude/commands/<name>.md` (synced) |
| Copilot | `.github/skills/` or `.github/prompts/` |
| Chain step | `chains/registry.yaml` → `steps[].invoke` |
| Orchestrator agent | Multi-lane plan delegates to skill/agent |
| Session-start | Envelope + thin host entrypoints |

**Platform rule:** Grok uses `.grok/`, Claude `.claude/`, Copilot `.github/`, etc. Shared code lives in `scripts/`.

## Catalog

### `acquire-codebase-knowledge`

- **Path:** `.grok/skills/acquire-codebase-knowledge/SKILL.md`
- **Title:** Acquire Codebase Knowledge
- **What / why:** Map, document, and onboard into any project codebase. Produces seven evidence-backed docs in docs/codebase/ using stack detection (25+ languages), CI/CD and container discovery, and inquiry checkpoints. Trigger for "map this codebase", "document architecture", "onboard me", "create codebase docs", /acquire-codebase-knowledge, or /read-codebase. Do not trigger for routine feature work unless the us
- **Invocation:** `/acquire-codebase-knowledge`; `/daily-standup`, `/load-project-cache-first`, `/read-codebase`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/acquire-codebase-knowledge/SKILL.md`

### `ai-content-guardrails`

- **Path:** `.grok/skills/ai-content-guardrails/SKILL.md`
- **Title:** AI Content Guardrails
- **What / why:** Defense in depth for prompt injection, PII leakage, and toxic content. Mandatory for all agents reading TODO, vault, reports, MCP output, or foreign transcripts. Use on /ai-content-guardrails, security audits, or when ingesting untrusted text.
- **Invocation:** `/ai-content-guardrails`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/ai-content-guardrails/SKILL.md`

### `ai-engineering-maturity`

- **Path:** `.grok/skills/ai-engineering-maturity/SKILL.md`
- **Title:** AI Engineering Maturity — 8 Stages Framework (project .grok)
- **What / why:** Framework for the 8 stages of AI engineering maturity (team and organization view). Based on the Upsun article by Fabien Potencier (https://upsun.com/blog/8-stages-ai-engineering-maturity/), which adapts Steve Yegge's individual "AI-assisted development" trust gradient into an organizational SDLC model. Use to assess adoption of AI tooling (Grok skills/agents/prompts, MCP, shared context, guardrai
- **Invocation:** `/ai-engineering-maturity`; `/daily-standup-with-cache`, `/load-project-cache-first`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/ai-engineering-maturity/SKILL.md`

### `amazon-ses-email`

- **Path:** `.grok/skills/amazon-ses-email/SKILL.md`
- **Title:** Amazon SES Email Setup for project Domain (Send + Receive)
- **What / why:** Full skill for setting up Amazon SES email for the project domain (sending + receiving). Non-Microsoft (AWS only). Integrated with Laravel mail config, DO hosting (droplet/App Platform), drift avoidance (project-drift-guardian + schema checks), security (least-privilege IAM, secrets), and billing flows. Use for initial domain setup, DNS records (DKIM/SPF/DMARC/MX), IAM user/keys or role, Laravel .
- **Invocation:** `/amazon-ses-email`; `/aws-route53-dns`, `/load-project-cache-first`, `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/amazon-ses-email/SKILL.md`

### `app-compound-gate`

- **Path:** `.grok/skills/app-compound-gate/SKILL.md`
- **Title:** App Compound Gate (session-start)
- **What / why:** Per-app compound learning gate for session-start: assess local loop spine (STATE, VISION, lessons-state), load durable lessons when READY, close SCAFFOLD or unclosed reports via loop-compound. No fleet audit — this repo only. L1: offer scaffold on GAP.
- **Invocation:** `/app-compound-gate`; `/app-compound-gate`, `/read-codebase`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/app-compound-gate/SKILL.md`

### `astro-expert`

- **Path:** `.grok/skills/astro-expert/SKILL.md`
- **Title:** Astro Expert
- **What / why:** Astro 4/5 expert: content collections, islands architecture, View Transitions, MDX, static/SSR/hybrid output, Tailwind integration. Cache-first. Use on /astro-expert or /chain web-design when manifest framework is astro.
- **Invocation:** `/astro-expert`; `/load-project-cache-first`, `/web-build-design`
- **Registry tier:** app
- **Registry path:** `.grok/skills/astro-expert/SKILL.md`

### `aws-route53-dns`

- **Path:** `.grok/skills/aws-route53-dns/SKILL.md`
- **Title:** AWS Route 53 DNS Setup for project Domains (Domains + Email Records + Verification)
- **What / why:** AWS Route 53 expert: hosted zones, production app DNS (A/CNAME/ALIAS), deploy-time DKIM/SPF/DMARC/MX for SES, nameserver delegation, DNS-as-code change batches. Coordinates perimeter firewalls with /digitalocean-app-platform-docr-deploy (DO Cloud Firewall) — Route 53 is DNS only, not firewall. Pairs with /amazon-ses-email, /github-workflow-expert, /git-workflow-guardrails. Cache-first.
- **Invocation:** `/aws-route53-dns`; `/amazon-ses-email`, `/digitalocean-app-platform-docr-deploy`, `/docker-expert`, `/eval/maintenance-task`, `/git-workflow-guardrails`, `/github-expert`, `/github-workflow-expert`, `/load-project-cache-first`, `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/aws-route53-dns/SKILL.md`

### `branch-context-agent`

- **Path:** `.grok/skills/branch-context-agent/SKILL.md`
- **Title:** Branch Context Agent
- **What / why:** Branch scope and TODO-alignment analyzer for project. Summarize branch purpose, changes vs active TODO, detect drift before merge or major work. Use when user runs /branch-context-agent or orchestrator needs context.
- **Invocation:** `/branch-context-agent`; `/load-project-cache-first`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/branch-context-agent/SKILL.md`

### `bug-hunter-agent`

- **Path:** `.grok/skills/bug-hunter-agent/SKILL.md`
- **Title:** Bug Hunter Agent
- **What / why:** Specialist bug and weakness hunter for any codebase: logic errors, edge cases, error handling, races, data integrity, config bugs, performance, integration gaps, and security surface triage. Fixes isolated issues or suggests patches with tests. Use on /bug-hunter-agent, "find bugs", "hunt bugs", "what could break", or in chains bug-hunt / bug-hunt-deep / bug-hunt-pre-deploy.
- **Invocation:** `/bug-hunter-agent`; `/branch-context-agent`, `/script-not-shell`, `/test-safety-agent`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/bug-hunter-agent/SKILL.md`

### `cache-efficient`

- **Path:** `.grok/skills/cache-efficient/SKILL.md`
- **Title:** Cache-Efficient Mode
- **What / why:** project cache-first session with minimal tokens: load INDEX + targeted cache/memories only, respond in short bullets. Use at every session start, when cost matters, or /cache-efficient. Default tone for this repo unless user asks for depth.
- **Invocation:** `/cache-efficient`; `/acquire-codebase-knowledge`, `/daily-standup-with-cache`, `/orchestrator`, `/read-codebase`, `/token-usage-meter`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/cache-efficient/SKILL.md`

### `cache-freshness-check`

- **Path:** `.grok/skills/cache-freshness-check/SKILL.md`
- **Title:** Cache Freshness Check
- **What / why:** Check docs/codebase cache freshness against manifest cache_stale_days, .codebase-scan.txt, README [UPDATED] markers, git branch, and TODO branch. Advises fresh/aging/stale/branch_drift and recommends /read-codebase or /chain cache-rebuild. Use on /cache-freshness-check, session-start, loop-triage, or before medium/high-risk orchestrator work.
- **Invocation:** `/cache-freshness-check`; `/branch-context-agent`, `/documentation-specialist`, `/load-project-cache-first`, `/loop-triage`, `/orchestrator`, `/read-codebase`, `/token-usage-meter`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/cache-freshness-check/SKILL.md`

### `chain`

- **Path:** `.grok/skills/chain/SKILL.md`
- **Title:** Chain — cache-first skill & prompt composition
- **What / why:** Discover and run token-efficient chains of skills and prompts using the cache. Auto-matches user intent to chains/registry.yaml (skills + chains catalog), executes steps with minimal handoffs. Always offers opt-out when ambiguous or if the user prefers a single skill. Registers logical custom chains to chains/registry.yaml. Use at /chain or when a task spans multiple skills.
- **Invocation:** `/chain`; `/cache-efficient`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/chain/SKILL.md`

### `changelog-specialist`

- **Path:** `.grok/skills/changelog-specialist/SKILL.md`
- **Title:** Changelog Specialist
- **What / why:** Incremental changelog for project: session log after every substantive action, consolidate into CHANGELOG.md [Unreleased] at EOD, generate PR body. Wired into /chain session-start (init) and eod-shutdown (consolidate + pr-body). Use on /changelog-specialist, after commits/features/fixes, or when user asks for changelog.
- **Invocation:** `/changelog-specialist`; `/changelog-specialist`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/changelog-specialist/SKILL.md`

### `copilot-instructions`

- **Path:** `.grok/skills/copilot-instructions/SKILL.md`
- **Title:** Copilot Instructions — Project Template (Grok Native)
- **What / why:** Core operational instructions for project (DDEV, security, data safety, TODO lifecycle, branch rules, auth regression, etc.). This is the native Grok skill (primary for Grok sessions). The `.github/copilot-instructions.md` version is maintained separately for GitHub Copilot users. Always reference the Grok version in .grok/ contexts.
- **Invocation:** `/ai-content-guardrails`, `/ai-engineering-maturity`, `/daily-standup`, `/daily-standup-with-cache`, `/prompt-patterns`

### `cyber-security-essentials`

- **Path:** `.grok/skills/cyber-security-essentials/SKILL.md`
- **Title:** Cyber Security Essentials (UK)
- **What / why:** UK NCSC Cyber Essentials compliance assessor for code, config, and CI. Maps five technical controls to application checks; complements security-audit, bug-hunter, and engineering skills. Use on /cyber-security-essentials, UK CE readiness, supplier assurance, or chains cyber-essentials-*.
- **Invocation:** `/cyber-security-essentials`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/cyber-security-essentials/SKILL.md`

### `daily-standup`

- **Path:** `.grok/skills/daily-standup/SKILL.md`
- **Title:** Daily Standup (alias)
- **What / why:** Alias for /daily-standup-with-cache. Start a daily session: fetch remote branches, report latest remote branch worked on, then cache + TODO + briefing.
- **Invocation:** `/daily-standup`; `/daily-standup-with-cache`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/daily-standup/SKILL.md`

### `daily-standup-with-cache`

- **Path:** `.grok/skills/daily-standup-with-cache/SKILL.md`
- **Title:** Daily Standup With Cache (Recommended Default Session Start)
- **What / why:** Start a daily working session on project using the local cache + today's TODO + open concerns. This is the recommended prompt/skill for almost every normal development or review session.
- **Invocation:** `/daily-standup-with-cache`; `/daily-standup-with-cache`, `/ddev-local-runtime`, `/read-codebase`, `/script-not-shell`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/daily-standup-with-cache/SKILL.md`

### `data-architect-expert`

- **Path:** `.grok/skills/data-architect-expert/SKILL.md`
- **Title:** Data Architect Expert
- **What / why:** Senior data architect: greenfield ER design, schema analysis and improvement, normalisation, indexing strategy, migration roadmaps. Produces mermaid ER diagrams and delegates engine implementation to mysql/mariadb/sqlite/vector experts. Cache-first. Use on /data-architect-expert or /chain database-design.
- **Invocation:** `/data-architect-expert`; `/load-project-cache-first`, `/mariadb-database-expert`, `/mysql-database-expert`, `/sqlite-database-expert`, `/vector-database-expert`
- **Registry tier:** app
- **Registry path:** `.grok/skills/data-architect-expert/SKILL.md`

### `ddev-cleanup`

- **Path:** `.grok/skills/ddev-cleanup/SKILL.md`
- **Title:** ddev-cleanup
- **What / why:** End-of-day cleanup for Grok Build + ddev projects. Repo status check, drift gate, ddev stop, cache/TODO update, commit and push on a feature branch, then reposition off master/develop for tomorrow. Use on shutdown, end of day, clean stop, daily cleanup.
- **Invocation:** `/ddev-cleanup`; `/branch-context-agent`, `/daily-standup-with-cache`, `/github-expert`, `/project-drift-guardian`, `/todo-specialist-agent`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/ddev-cleanup/SKILL.md`

### `ddev-local-runtime`

- **Path:** `.grok/skills/ddev-local-runtime/SKILL.md`
- **Title:** DDEV is the local runtime — host shell is not supported
- **What / why:** Mandatory rule that all local project commands for the project repository run inside the DDEV runtime, not on the host shell. Apply when about to run php, composer, artisan, npm, node, python3, pip, mysql, pest, phpunit, or any project tooling locally.
- **Invocation:** `/ddev-local-runtime`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/ddev-local-runtime/SKILL.md`

### `didit-identity-integration`

- **Path:** `.grok/skills/didit-identity-integration/SKILL.md`
- **Title:** Didit Identity Integration (KYC / KYB / AML)
- **What / why:** Full skill for Didit identity verification (KYC, KYB, AML, biometrics) in Laravel app repos. Sessions API + SDK or standalone modules; programmatic account; HMAC webhook verification. Canonical API facts in references/; copy-paste export in exports/. Integrated with project-drift-guardian, security-audit-agent, laravel-expert-agent, cache-first. Use for signer verification, age gates, re-auth, com
- **Invocation:** `/didit-identity-integration`; `/load-project-cache-first`, `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/didit-identity-integration/SKILL.md`

### `digitalocean-app-platform-docr-deploy`

- **Path:** `.grok/skills/digitalocean-app-platform-docr-deploy/SKILL.md`
- **Title:** DigitalOcean DevOps Expert — Hosting, CI Deploy & DB Update (No-Drift)
- **What / why:** Senior DigitalOcean DevOps expert for project hosting (App Platform + DOCR and/or Droplets), CI/CD via GitHub Actions, safe database updates, and no-drift deploy gates. Integrates /git-workflow-guardrails and /github-expert for every delivery path. Deep doctl, networking, token-scoping, and troubleshooting knowledge. Use for initial setup, workflow creation, deploy, DB migrate, or production incid
- **Invocation:** `/digitalocean-app-platform-docr-deploy`; `/aws-route53-dns`, `/branch-context-agent`, `/cache-efficient`, `/ddev-local-runtime`, `/docker-expert`, `/eval/maintenance-task`, `/git-workflow-guardrails`, `/github-expert`, `/github-workflow-expert`, `/load-project-cache-first`, `/model-schema-check`, `/prod-db-maintenance`
- **Registry tier:** app
- **Registry path:** `.grok/skills/digitalocean-app-platform-docr-deploy/SKILL.md`

### `docker-expert`

- **Path:** `.grok/skills/docker-expert/SKILL.md`
- **Title:** Docker Expert — Local & Hardened Production Deploy
- **What / why:** Docker expert for local dev and production deploy: multi-stage hardened images, minimal runtime layers, .dockerignore discipline, non-root users. Pairs with github-workflow-expert (build/push CI), github-expert (policy), git-workflow-guardrails (commits), and digitalocean-app-platform-docr-deploy (DOCR/App Platform). Cache-first.
- **Invocation:** `/docker-expert`; `/digitalocean-app-platform-docr-deploy`, `/git-workflow-guardrails`, `/github-expert`, `/github-workflow-expert`, `/load-project-cache-first`, `/project-drift-guardian`, `/security-audit-agent`
- **Registry tier:** app
- **Registry path:** `.grok/skills/docker-expert/SKILL.md`

### `documentation-specialist`

- **Path:** `.grok/skills/documentation-specialist/SKILL.md`
- **Title:** Documentation Specialist
- **What / why:** Full-project documentation maker for orchestrator template or any forked app repo. Produces a GitHub Docs-style navigable site (docs/index.md + sections) plus agent cache. Uses /chain to compose load-cache, read-codebase, and readme-specialist. No secrets, trade secrets, or coding tips in output. Invoke /documentation-specialist or /chain documentation-full. Docs only — no source edits.
- **Invocation:** `/documentation-specialist`; `/chain`, `/read-codebase`, `/readme-specialist`, `/script-not-shell`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/documentation-specialist/SKILL.md`

### `docx`

- **Path:** `.grok/skills/docx/SKILL.md`
- **Title:** DOCX creation, editing, and analysis
- **What / why:** Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of
- **Invocation:** `/docx`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/docx/SKILL.md`

### `eval-maintenance-task`

- **Path:** `.grok/skills/eval/maintenance-task/SKILL.md`
- **Title:** Eval: Maintenance Task (AI Engineering Maturity)
- **What / why:** Post-maintenance evaluation skill for production readiness tasks (registry cleanup, DB imports, live listings freshness, etc.). Uses the 8 stages AI engineering maturity lens: moves "standards" (success criteria, protection of active data, freshness) out of heads and into the system as first-class evals (Stage 5/8). Always run after one-off or recurring maintenance to produce auditable reports.
- **Invocation:** `/eval-maintenance-task`; `/ai-engineering-maturity`, `/daily-standup-with-cache`, `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/eval/maintenance-task/SKILL.md`

### `filament-panel-review`

- **Path:** `.grok/skills/filament-panel-review/SKILL.md`
- **Title:** Filament Panel Review (Cache-First)
- **What / why:** Review one or more of the 7 Filament 5 panels in project multi-panel architecture using the local cache first. Use for panel audits, resource reviews, widget checks, cross-panel reuse, or before changes to providers/resources.
- **Invocation:** `/filament-panel-review`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/filament-panel-review/SKILL.md`

### `frontend-web-design-expert`

- **Path:** `.grok/skills/frontend-web-design-expert/SKILL.md`
- **Title:** Frontend Web Design Expert
- **What / why:** Framework-agnostic UI/UX expert: HTML, Tailwind, design tokens, responsive layouts, and WCAG AA a11y. Default is server-rendered UI (Blade, Livewire, HTMX, Filament, Go templates) — not a separate SPA. Complements /web-build-design. Routes to stack experts only when manifest requires. Cache-first. Use on /frontend-web-design-expert, /frontend-expert, or /chain frontend-ui.
- **Invocation:** `/frontend-web-design-expert`; `/astro-expert`, `/filament-panel-review`, `/go-expert`, `/laravel-expert-agent`, `/load-project-cache-first`, `/nextjs-expert`, `/nuxt-expert`, `/web-build-design`, `/webapp-testing`
- **Registry tier:** app
- **Registry path:** `.grok/skills/frontend-web-design-expert/SKILL.md`

### `git-workflow-guardrails`

- **Path:** `.grok/skills/git-workflow-guardrails/SKILL.md`
- **Title:** Git Workflow Guardrails
- **What / why:** Git and githooks workflow for safe delivery. Use when committing, pushing, tagging, releasing, or preparing PR. Enforces secrets/env guard before commit/push, security checklist, tests, clear commits, branch promotion (feature->develop->master), annotated tags.
- **Invocation:** `/git-workflow-guardrails`; `/github-ci-readiness-expert`, `/load-project-cache-first`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/git-workflow-guardrails/SKILL.md`

### `github-ci-readiness-expert`

- **Path:** `.grok/skills/github-ci-readiness-expert/SKILL.md`
- **Title:** GitHub CI/CD Branch Readiness Expert
- **What / why:** GitHub CI/CD branch readiness expert for wave projects. Analyses the current branch against .github/workflows triggers, secret names, Node 24 policy, and local parity (chain-audit). Per-project rules live in references/<slug>-ci.md. Chains with /github-expert and /git-workflow-guardrails via /chain ci-branch-readiness. Sign-off READY | CONDITIONAL | BLOCKED before push or PR. Use on /github-ci-rea
- **Invocation:** `/github-ci-readiness-expert`; `/git-workflow-guardrails`, `/github-expert`, `/github-workflow-expert`, `/load-project-cache-first`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/github-ci-readiness-expert/SKILL.md`

### `github-expert`

- **Path:** `.grok/skills/github-expert/SKILL.md`
- **Title:** GitHub Expert Agent
- **What / why:** GitHub platform expert for project workflows, Actions, PRs, security scanning, automation. Use when /github-expert or managing CI/deploy. For programmatic workflow CRUD and secrets management, delegate to /github-workflow-expert.
- **Invocation:** `/github-expert`; `/git-workflow-guardrails`, `/github-workflow-expert`, `/load-project-cache-first`, `/prompt-patterns`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/github-expert/SKILL.md`

### `github-workflow-expert`

- **Path:** `.grok/skills/github-workflow-expert/SKILL.md`
- **Title:** GitHub Workflow Expert — Programmatic Actions & Secrets
- **What / why:** Programmatic GitHub Actions expert: create, amend, delete workflows in .github/workflows/, manage repo and environment secrets via gh CLI, dispatch and enable/disable workflows. Use for /github-workflow-expert, "set GH secrets", "add deploy workflow", "remove workflow", or CI automation tasks. Pairs with /docker-expert (hardened image CI), /git-workflow-guardrails for commits, and /github-expert f
- **Invocation:** `/github-workflow-expert`; `/digitalocean-app-platform-docr-deploy`, `/git-workflow-guardrails`, `/github-ci-readiness-expert`, `/github-expert`, `/load-project-cache-first`, `/project-drift-guardian`, `/security-audit-agent`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/github-workflow-expert/SKILL.md`

### `go-expert`

- **Path:** `.grok/skills/go-expert/SKILL.md`
- **Title:** Go Expert
- **What / why:** Go 1.22+ expert: stdlib HTTP, chi/gin/echo (project-existing), sqlc/GORM, modules, testing, observability, Docker. Cache-first. Use on /go-expert for APIs, CLIs, and static/marketing backends when manifest language is go.
- **Invocation:** `/go-expert`; `/data-architect-expert`, `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/go-expert/SKILL.md`

### `jersey-aml-compliance-expert`

- **Path:** `.grok/skills/jersey-aml-compliance-expert/SKILL.md`
- **Title:** Jersey AML / Compliance Expert (POCL + Money Laundering Order)
- **What / why:** Expert on Jersey anti-money laundering, counter-terrorist financing and counter-proliferation financing (AML/CFT/CPF). Primary sources: Proceeds of Crime (Jersey) Law 1999 (POCL) and Money Laundering (Jersey) Order 2008 (MLO). Covers Schedule 2 scope, customer due diligence (CDD/EDD), risk assessments, MLRO/MLCO obligations, record keeping, suspicious activity reporting (SARs) to JFCU, tipping-off
- **Invocation:** _(see SKILL.md)_

### `jersey-data-protection-expert`

- **Path:** `.grok/skills/jersey-data-protection-expert/SKILL.md`
- **Title:** Jersey Data Protection Expert
- **What / why:** Expert on the Data Protection (Jersey) Law 2018 (DPJL) and the Data Protection Authority (Jersey) Law 2018. Covers principles, lawful bases, data subject rights, DPIAs, breach notification, international transfers, accountability, registration, enforcement, and practical implementation guidance for systems and applications (especially Jersey-based or processing Jersey personal data). References of
- **Invocation:** _(see SKILL.md)_

### `laravel-expert-agent`

- **Path:** `.grok/skills/laravel-expert-agent/SKILL.md`
- **Title:** Laravel Expert Agent
- **What / why:** Laravel 12 + Filament 5 expert for project. Use for architecture, resources, Eloquent, panels, services, Artisan, testing, or when /laravel-expert-agent.
- **Invocation:** `/laravel-expert-agent`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/laravel-expert-agent/SKILL.md`

### `llm-wiki`

- **Path:** `.grok/skills/llm-wiki/SKILL.md`
- **Title:** LLM Wiki
- **What / why:** Karpathy-style LLM wiki: ingest raw sources into a persistent markdown wiki, query with index-first navigation, lint for contradictions/orphans/stale pages. Use on /llm-wiki, /wiki, or chains wiki-ingest / wiki-query / wiki-lint. Honors wiki_policy in the project manifest (mode off|lean|full).
- **Invocation:** `/llm-wiki`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/llm-wiki/SKILL.md`

### `load-project-cache-first`

- **Path:** `.grok/skills/load-project-cache-first/SKILL.md`
- **Title:** Load Local Codebase Cache First (Token-Efficient Session Start)
- **What / why:** Load project project cache (docs/codebase/ + TODO + CONCERNS + .grok/.copilot memories) first before any deep exploration. Use at the start of almost every session to save tokens and provide accurate context quickly. Mandatory entry point for ongoing work.
- **Invocation:** `/load-project-cache-first`; `/acquire-codebase-knowledge`, `/app-compound-gate`, `/cache-freshness-check`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/load-project-cache-first/SKILL.md`

### `loop-compound`

- **Path:** `.grok/skills/loop-compound/SKILL.md`
- **Title:** Loop Compound (steps 10–14)
- **What / why:** Compound learning closure (14-step roadmap steps 10–14): capture loop lessons, promote to STATE.md + secure hash-chained vault graph (reports/vault/events.jsonl with content hashes, provenance, secret scrubbing), record gates, queue promotions. Run after loop-verifier PASS. Cache-first; L1 report-only + human approval for mutations. Strong integrity via verify_ledger.
- **Invocation:** `/loop-compound`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/loop-compound/SKILL.md`

### `loop-engineering`

- **Path:** `.grok/skills/loop-engineering/SKILL.md`
- **Title:** Loop Engineering (orchestrator template)
- **What / why:** Loop engineering for this template: design systems that prompt agents, not hand prompts. Cache is king — all loops are cache-first. Assess maturity, pick next pattern, run loop-audit. See LOOP.md, patterns/, and loop-budget.md.
- **Invocation:** `/loop-engineering`; `/acquire-codebase-knowledge`, `/cache-efficient`, `/chain`, `/documentation-specialist`, `/goal`, `/load-project-cache-first`, `/loop-compound`, `/loop-triage`, `/loop-verifier`, `/orchestrator`, `/skill-creator`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/loop-engineering/SKILL.md`

### `loop-triage`

- **Path:** `.grok/skills/loop-triage/SKILL.md`
- **Title:** Loop Triage (L1, cache-first)
- **What / why:** L1 daily loop triage for the orchestrator template. Cache is king: load manifest + lean cache before any source or gh deep-dive. Synthesise priorities into STATE.md and reports/loops/. Report-only; no auto-fix. Use on schedule or /loop-triage.
- **Invocation:** `/loop-triage`; `/cache-freshness-check`, `/loop-compound`, `/loop-verifier`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/loop-triage/SKILL.md`

### `loop-verifier`

- **Path:** `.grok/skills/loop-verifier/SKILL.md`
- **Title:** Loop Verifier (maker/checker split)
- **What / why:** Independent verifier for loop outputs. Checks artifacts and rubric only — not maker reasoning. Enforces cache citations, L1 no-auto-fix, and loop-budget compliance. Use after loop-triage.
- **Invocation:** `/loop-verifier`; `/loop-compound`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/loop-verifier/SKILL.md`

### `loqate-address-integration`

- **Path:** `.grok/skills/loqate-address-integration/SKILL.md`
- **Title:** Loqate Address Capture Integration
- **What / why:** Full skill for Loqate (GBG) Address Capture in Laravel app repos. Find + Retrieve type-ahead via backend proxy; normalized address storage. Canonical API in references/; export prompt in exports/. Integrated with project-drift-guardian, security-audit-agent, laravel-expert-agent, cache-first. Use for signer addresses, billing/checkout address, proof-of-address fields in e-ndsign or ndestates-io.
- **Invocation:** `/loqate-address-integration`; `/load-project-cache-first`, `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/loqate-address-integration/SKILL.md`

### `mariadb-database-expert`

- **Path:** `.grok/skills/mariadb-database-expert/SKILL.md`
- **Title:** MariaDB Database Expert
- **What / why:** MariaDB 10.x/11.x expert for project: InnoDB/Aria, Galera, replication, JSON, spatial, Laravel Eloquent, Python connectors. Schema, tuning, migrations safety. Use on /mariadb-database-expert or when manifest database_engine is mariadb/mysql-compatible MariaDB.
- **Invocation:** `/mariadb-database-expert`; `/data-architect-expert`, `/load-project-cache-first`, `/model-schema-check`, `/schema-audit-agent`, `/sqlite-database-expert`, `/test-safety-agent`
- **Registry tier:** app
- **Registry path:** `.grok/skills/mariadb-database-expert/SKILL.md`

### `model-schema-check`

- **Path:** `.grok/skills/model-schema-check/SKILL.md`
- **Title:** Model Schema Check (Cache-First + Safe)
- **What / why:** Review model vs database schema consistency on project using the local cache and project tooling. Use before/after migrations or when schema drift is suspected. Strictly test DB only.
- **Invocation:** `/model-schema-check`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/model-schema-check/SKILL.md`

### `mysql-concurrency-test`

- **Path:** `.grok/skills/mysql-concurrency-test/SKILL.md`
- **Title:** MySQL Concurrency Tests (Laravel/Eloquent)
- **What / why:** Design MySQL concurrency tests adapted for Laravel 12 + Eloquent (lockForUpdate, DB::transaction, queues, optimistic/pessimistic locking). Includes reusable prompt. Use when modeling race conditions on stock, balances, orders etc. Complements /mysql-database-expert and /laravel-expert-agent.
- **Invocation:** `/laravel-expert-agent`, `/mysql-database-expert`, `/test-safety-agent`

### `mysql-database-expert`

- **Path:** `.grok/skills/mysql-database-expert/SKILL.md`
- **Title:** MySQL Database Expert
- **What / why:** MySQL 8.x expert for project: InnoDB, JSON, window functions, CTEs, replication, Laravel Eloquent, Python connectors. Schema, EXPLAIN, indexing, migrations safety. Use on /mysql-database-expert or /chain migration-safe. Cache-first.
- **Invocation:** `/mysql-database-expert`; `/data-architect-expert`, `/load-project-cache-first`, `/mariadb-database-expert`, `/model-schema-check`, `/sqlite-database-expert`, `/vector-database-expert`
- **Registry tier:** app
- **Registry path:** `.grok/skills/mysql-database-expert/SKILL.md`

### `nextjs-expert`

- **Path:** `.grok/skills/nextjs-expert/SKILL.md`
- **Title:** Next.js Expert
- **What / why:** Next.js 14/15 App Router expert: RSC, server actions, route handlers, middleware, Tailwind, auth patterns, Vercel/Node deploy. Cache-first. Use on /nextjs-expert or /chain web-design when manifest framework is nextjs.
- **Invocation:** `/nextjs-expert`; `/data-architect-expert`, `/load-project-cache-first`, `/web-build-design`
- **Registry tier:** app
- **Registry path:** `.grok/skills/nextjs-expert/SKILL.md`

### `nuxt-expert`

- **Path:** `.grok/skills/nuxt-expert/SKILL.md`
- **Title:** Nuxt Expert
- **What / why:** Nuxt 3/4 expert: file-based routing, server routes, composables, Pinia, Nitro, SSR/SSG/prerender, Tailwind module. Cache-first. Use on /nuxt-expert or /chain web-design when manifest framework is nuxt or nuxtjs.
- **Invocation:** `/nuxt-expert`; `/load-project-cache-first`, `/web-build-design`
- **Registry tier:** app
- **Registry path:** `.grok/skills/nuxt-expert/SKILL.md`

### `orchestrator-deploy`

- **Path:** `.grok/skills/orchestrator-deploy/SKILL.md`
- **Title:** Orchestrator Deploy
- **What / why:** Deploy orchestrator .grok skills, prompts, agents, and root chains (CHAIN.md, chains/registry.yaml) to any target project. Tracks customized files in deploy-state.json; prompts overwrite, skip, or merge on conflict. Pre-deploy backups with --rollback. Selectable bundles include .claude and .copilot. Use with /orchestrator-deploy or /chain template-deploy. Fleet: explicit approval only; never copy 
- **Invocation:** `/orchestrator-deploy`; `/git-workflow-guardrails`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/orchestrator-deploy/SKILL.md`

### `paypal-billing-integration`

- **Path:** `.grok/skills/paypal-billing-integration/SKILL.md`
- **Title:** PayPal Billing & Payments Integration for project (Non-Microsoft)
- **What / why:** Full skill for PayPal integration in project for payments and generating billing documents (invoices, receipts) directly at PayPal. Non-Microsoft (pure PayPal + Laravel). Use for checkout flows (e.g. admin subscriptions or document requests), webhook handling (payments, disputes), generating/sending PayPal invoices tied to e-sign usage, and refunds. Integrated with DO hosting, drift avoidance (pro
- **Invocation:** `/paypal-billing-integration`; `/load-project-cache-first`, `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/paypal-billing-integration/SKILL.md`

### `prod-db-maintenance`

- **Path:** `.grok/skills/prod-db-maintenance/SKILL.md`
- **Title:** Prod DB Maintenance (Stage 6: Operating System)
- **What / why:** Skill for invoking import or update of the production database as Stage 6 infrastructure (operating system). Treats DB maintenance as a first-class "agent slot" task: spec-driven, heavily cache-backed, followed by /eval-maintenance-task, with observability. Maximizes shared context (docs/codebase, TODO, previous evals, architecture, mysql expert) to avoid "ten things" and ensure clean prod state. 
- **Invocation:** `/prod-db-maintenance`; `/ai-engineering-maturity`, `/daily-standup-with-cache`, `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/prod-db-maintenance/SKILL.md`

### `project-drift-guardian`

- **Path:** `.grok/skills/project-drift-guardian/SKILL.md`
- **Title:** Project Drift Guardian (project)
- **What / why:** Specialized guardian against project drift for project. Uses GitHub branches for work isolation, persistent database (or app DB table) for requirements tracking (e-sign features, signing flows, audit/compliance), and Grok reviews for alignment checks. Enforces pre-deploy drift scans (code, schema, container tags, scope) to avoid drift at all costs. Trigger on planning, feature dev, scope reviews, 
- **Invocation:** `/project-drift-guardian`
- **Registry tier:** app
- **Registry path:** `.grok/skills/project-drift-guardian/SKILL.md`

### `prompt-patterns`

- **Path:** `.grok/skills/prompt-patterns/SKILL.md`
- **Title:** Prompt Patterns
- **What / why:** High-signal prompt engineering patterns (grounded RAG with refusal, Socratic code review, strict formatting, complex structure). Invocable via /prompt-patterns. Use when authoring skills/prompts/agents/graders. Full reference: reports/research/prompt-patterns.md + .grok/prompts/prompt-patterns.md
- **Invocation:** `/prompt-patterns`; `/prompt-patterns`
- **Registry tier:** app
- **Registry path:** `.grok/skills/prompt-patterns/SKILL.md`

### `qa-agent`

- **Path:** `.grok/skills/qa-agent/SKILL.md`
- **Title:** QA Agent (Full Agent)
- **What / why:** Full QA agent (reusable general structure + per-wave-project specializations). Specializations live in references/<project>-specializations.md (facebook-stats, google-stats, e-ndsign, ndestates-io, lightstone, ...). Performs comprehensive quality assessment including functional correctness, test adequacy, structural maintainability, domain risks, safety/compliance (DDEV + test DB only), and produc
- **Invocation:** `/qa-agent`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/qa-agent/SKILL.md`

### `read-codebase`

- **Path:** `.grok/skills/read-codebase/SKILL.md`
- **Title:** Read Codebase (alias)
- **What / why:** Backward-compatible alias for acquire-codebase-knowledge. Full codebase scan with stack detection, seven docs/codebase/ files, and cache refresh. Use for onboarding, major cache refresh, or /read-codebase. Rare for daily work.
- **Invocation:** `/read-codebase`; `/acquire-codebase-knowledge`, `/read-codebase`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/read-codebase/SKILL.md`

### `readme-specialist`

- **Path:** `.grok/skills/readme-specialist/SKILL.md`
- **Title:** README Specialist
- **What / why:** Documentation specialist for project README, guides, reference/*.md . Limited to docs only. Use on /readme-specialist or when improving project docs.
- **Invocation:** `/readme-specialist`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/readme-specialist/SKILL.md`

### `research-deep-dive`

- **Path:** `.grok/skills/research-deep-dive/SKILL.md`
- **Title:** Research Deep Dive
- **What / why:** Optional external-topic research before implementation. Frame with multi-lens questions, gather from cache and user-approved sources only (no default web), write a short memo under reports/research/. Not for codebase onboarding. Use on /research-deep-dive or /chain research-deep-dive. STORM-inspired questioning only — no STORM product.
- **Invocation:** `/research-deep-dive`; `/acquire-codebase-knowledge`, `/chain`, `/orchestrator`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/research-deep-dive/SKILL.md`

### `schema-audit-agent`

- **Path:** `.grok/skills/schema-audit-agent/SKILL.md`
- **Title:** Schema Audit Agent
- **What / why:** Read-only schema/migration auditor for project. Use on /schema-audit-agent or for drift analysis.
- **Invocation:** `/schema-audit-agent`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/schema-audit-agent/SKILL.md`

### `script-not-shell`

- **Path:** `.grok/skills/script-not-shell/SKILL.md`
- **Title:** Script-Not-Shell (avoid escaping failures)
- **What / why:** Avoid inline shell escaping failures by writing script files first. Use when running multi-line Python/bash, heredocs, nested quotes, YAML/JSON in shell, audit logic, or after heredoc/syntax errors. Creates temp scripts (/tmp) or permanent scripts (scripts/). Invoke with /script-not-shell. Reduces retry loops and token waste.
- **Invocation:** `/script-not-shell`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/script-not-shell/SKILL.md`

### `security-audit-agent`

- **Path:** `.grok/skills/security-audit-agent/SKILL.md`
- **Title:** Security Audit Agent
- **What / why:** Security, auth, permissions, CDD/consent auditor for project. Use on /security-audit-agent , post-dep or form changes.
- **Invocation:** `/security-audit-agent`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/security-audit-agent/SKILL.md`

### `session-resume`

- **Path:** `.grok/skills/session-resume/SKILL.md`
- **Title:** Session Resume (resume-first)
- **What / why:** Resume-first gate for session-start: when a fresh resume card exists, trust it for branch/done/open/cache and skip redundant TODO/STATE/git reads to save tokens. Use on /chain session-start, /daily-standup-with-cache, or when user pastes a resume card.
- **Invocation:** `/session-resume`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/session-resume/SKILL.md`

### `skill-creator`

- **Path:** `.grok/skills/skill-creator/SKILL.md`
- **Title:** Skill Creator (orchestrator)
- **What / why:** Create new skills, modify and improve existing skills, and measure skill performance with quantitative evals, parallel subagent runs (with/without or old/new baselines), grading, benchmark aggregation (mean ± stddev), human review, and description optimization for better triggering. High token cost — use with approval and token-usage-meter. For developing .grok/skills/ primitives that power loops 
- **Invocation:** `/skill-creator`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/skill-creator/SKILL.md`

### `sqlite-database-expert`

- **Path:** `.grok/skills/sqlite-database-expert/SKILL.md`
- **Title:** SQLite Database Expert
- **What / why:** SQLite expert for project: embedded DB, Laravel :memory:/file drivers, Python sqlite3, WAL mode, migrations, FTS5, strict tables. Use on /sqlite-database-expert or when manifest database_engine is sqlite or tests use in-memory SQLite.
- **Invocation:** `/sqlite-database-expert`; `/data-architect-expert`, `/load-project-cache-first`, `/mariadb-database-expert`, `/mysql-database-expert`, `/schema-audit-agent`, `/test-safety-agent`
- **Registry tier:** app
- **Registry path:** `.grok/skills/sqlite-database-expert/SKILL.md`

### `template-decontaminate`

- **Path:** `.grok/skills/template-decontaminate/SKILL.md`
- **Title:** Template Decontaminate
- **What / why:** Post-deploy, pre-commit gate for forked app repos. After the orchestrator template is deployed, renames skills/prompts/agents to the target project (slug = target dir name, e.g. /home/nickd/projects/orchestrator -> orchestrator) via customize-skills-for-project.py, then HARD-GATE scans for leftover template identifiers and unresolved placeholders. Blocks commit and notifies on residue. Use with /t
- **Invocation:** `/template-decontaminate`; `/orchestrator-deploy`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/template-decontaminate/SKILL.md`

### `test-safety-agent`

- **Path:** `.grok/skills/test-safety-agent/SKILL.md`
- **Title:** Test Safety Agent
- **What / why:** Enforce test DB safety and pre/post risk assessment for project tests. Use before running tests or on /test-safety-agent.
- **Invocation:** `/test-safety-agent`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/test-safety-agent/SKILL.md`

### `test-specialist-agent`

- **Path:** `.grok/skills/test-specialist-agent/SKILL.md`
- **Title:** Test Specialist Agent
- **What / why:** Write/improve/convert tests (Pest preferred) for project. Preserves logic; follows safety. Use on /test-specialist-agent or test tasks.
- **Invocation:** `/test-specialist-agent`; `/load-project-cache-first`
- **Registry tier:** app
- **Registry path:** `.grok/skills/test-specialist-agent/SKILL.md`

### `todo-specialist-agent`

- **Path:** `.grok/skills/todo-specialist-agent/SKILL.md`
- **Title:** TODO Specialist Agent
- **What / why:** Maintain project TODO-*.md (carry forward, prioritize, update from work). Use on /todo-specialist-agent or when syncing tasks.
- **Invocation:** `/todo-specialist-agent`; `/load-project-cache-first`
- **Registry tier:** shared
- **Registry path:** `.grok/skills/todo-specialist-agent/SKILL.md`

### `token-usage-meter`

- **Path:** `.grok/skills/token-usage-meter/SKILL.md`
- **Title:** Token Usage Meter
- **What / why:** Always-on xAI/Grok token usage and prompt-cache monitor. Syncs session context from Grok updates.jsonl, logs trends to reports/tokens/, warns on context bloat and cache misses. Surface a one-line Token meter footer on every substantive response when monitoring is enabled. Use on /token-usage-meter, session-start, eod-shutdown, or when user asks about token cost.
- **Invocation:** `/token-usage-meter`; `/cache-efficient`, `/token-usage-meter`
- **Registry tier:** orchestrator
- **Registry path:** `.grok/skills/token-usage-meter/SKILL.md`

### `vector-database-expert`

- **Path:** `.grok/skills/vector-database-expert/SKILL.md`
- **Title:** Vector Database Expert
- **What / why:** Vector database expert: fit assessment (should this project use vectors?), then pgvector, Qdrant, Pinecone, Weaviate, Chroma, RAG schema, hybrid search. Cache-first. Use on /vector-database-expert, /chain vector-db-assess, or /chain vector-db-setup.
- **Invocation:** `/vector-database-expert`; `/data-architect-expert`, `/load-project-cache-first`, `/mysql-database-expert`, `/security-audit-agent`
- **Registry tier:** app
- **Registry path:** `.grok/skills/vector-database-expert/SKILL.md`

### `web-build-design`

- **Path:** `.grok/skills/web-build-design/SKILL.md`
- **Title:** Web Build & Design (multi-framework)
- **What / why:** Web build & design lead: conversion-focused SaaS marketing, pricing, portals. Routes implementation per manifest — Laravel/Blade/Livewire and Go templates are the default; Next/Astro/Nuxt only when the project uses them. Creative-tim inspired aesthetics. Cache-first. Use on /web-build-design or /chain web-design.
- **Invocation:** `/web-build-design`; `/astro-expert`, `/download`, `/frontend-web-design-expert`, `/go-expert`, `/laravel-expert-agent`, `/licensing`, `/load-project-cache-first`, `/nextjs-expert`, `/nuxt-expert`, `/paypal-billing-integration`, `/products`
- **Registry tier:** app
- **Registry path:** `.grok/skills/web-build-design/SKILL.md`

### `webapp-testing`

- **Path:** `.grok/skills/webapp-testing/SKILL.md`
- **Title:** Web Application Testing
- **What / why:** Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
- **Invocation:** `/webapp-testing`
- **Registry tier:** app
- **Registry path:** `.grok/skills/webapp-testing/SKILL.md`
