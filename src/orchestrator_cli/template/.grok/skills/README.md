# `.grok/skills/` — Grok slash commands (orchestrator template + forked app skills)

**Source of truth** for project skills. Synced to `.github/skills/`, `.copilot/skills/`, and `.claude/commands/` via `scripts/sync_grok_to_github_claude.py`.

- Machine catalog (skills + chains): [`chains/registry.yaml`](../../chains/registry.yaml)
- Prompts: [`.grok/prompts/`](../prompts/)
- Agents: [`.grok/agents/`](../agents/)

Each `SKILL.md` with `user-invocable: true` appears as `/<name>` in Grok. **New skills must be added to `chains/registry.yaml` (skills section) and this README**, then sync.

**Explicit tooling (Grok):** All skills now declare `allowed-tools:` in frontmatter for least privilege (bash, read_file, edit_file, write_file, web_search, ...). See `docs/reference/tools.md`. Update skill-creator to enforce for new skills. Manifests are platform-specific (`.grok/project-manifest.yaml` for Grok sessions — always read first at session start).

A JSON Schema is included (`schemas/skill.schema.json`) and wired in `.vscode/settings.json` so VSCode no longer complains about `allowed-tools` (and provides autocomplete).

## Orchestrator template (tier: orchestrator)

| Slash | Source | Use when |
|-------|--------|----------|
| `/script-not-shell` | [`script-not-shell/SKILL.md`](script-not-shell/SKILL.md) | Multi-line shell, heredocs, nested quotes, or prior syntax errors — **write `scripts/` or `/tmp/agent-*` first** (CONCERNS §6) |
| `/chain` | [`chain/SKILL.md`](chain/SKILL.md) | Compose skills from `chains/registry.yaml` |
| `/cache-efficient` | [`cache-efficient/SKILL.md`](cache-efficient/SKILL.md) | Lean token mode (default tone) |
| `/cache-freshness-check` | [`cache-freshness-check/SKILL.md`](cache-freshness-check/SKILL.md) | Cache age vs policy, branch drift; includes `scripts/cache_freshness_check.py` |
| `/token-usage-meter` | [`token-usage-meter/SKILL.md`](token-usage-meter/SKILL.md) | xAI usage JSON + cache hit rate; `scripts/analyze_token_usage.py` |
| `/loop-triage` | [`loop-triage/SKILL.md`](loop-triage/SKILL.md) | L1 daily triage |
| `/loop-verifier` | [`loop-verifier/SKILL.md`](loop-verifier/SKILL.md) | Verify loop artifacts |
| `/loop-engineering` | [`loop-engineering/SKILL.md`](loop-engineering/SKILL.md) | Loop patterns + `loop-audit.sh` |
| `/skill-creator` | [`skill-creator/SKILL.md`](skill-creator/SKILL.md) | Create/iterate/benchmark skills with evals + subagents (meta for loop engineering). High cost; see plan in reports/. |
| `/skill-health` | [`skill-health/SKILL.md`](skill-health/SKILL.md) | Score log + `verified_at`/`covers` drift for the self-regulating cohort |
| `/find-skills` | [`find-skills/SKILL.md`](find-skills/SKILL.md) | Discover complementary skills on skills.sh **after** the local catalog; never raw-install into the template |
| `/grill-me` | [`grill-me/SKILL.md`](grill-me/SKILL.md) | Relentless design-tree interview before building; user owns decisions, agent looks up facts |
| `/teach` | [`teach/SKILL.md`](teach/SKILL.md) | Multi-session teaching workspace under `reports/teach/<slug>/` |
| `/systematic-debugging` | [`systematic-debugging/SKILL.md`](systematic-debugging/SKILL.md) | Root-cause process for a *known* bug or test failure (not a whole-repo hunt) |
| `/verification-before-completion` | [`verification-before-completion/SKILL.md`](verification-before-completion/SKILL.md) | Fresh proof command before any done/fixed/passing claim |
| `/ddev-cleanup` | [`ddev-cleanup/SKILL.md`](ddev-cleanup/SKILL.md) | End-of-day shutdown |
| `/documentation-specialist` | [`documentation-specialist/SKILL.md`](documentation-specialist/SKILL.md) | Full project docs; uses `/chain documentation-full` or `documentation-refresh` |
| `/docx` | [`docx/SKILL.md`](docx/SKILL.md) | Create/read/edit .docx Word docs (docx-js, XML unpack/edit/pack, pandoc, LibreOffice) |
| `/orchestrator-deploy` | [`orchestrator-deploy/SKILL.md`](orchestrator-deploy/SKILL.md) | Deploy .grok + chains to target; conflict: overwrite/skip/merge |

## Documentation chains

| Chain | Steps | Use when |
|-------|-------|----------|
| `documentation-full` | load-cache → read-codebase → readme-specialist → documentation-specialist | Onboarding, stale cache, full doc set |
| `documentation-refresh` | load-cache → readme-specialist → documentation-specialist | Update docs from current cache |

Invoke: `/chain documentation-full` or `/documentation-specialist full`

## Session start commands

| Slash command | Source | Use when |
|---------------|--------|----------|
| `/load-project-cache-first` | `.grok/prompts/load-project-cache-first.md` + skill | Every session; before specialized work. Loads INDEX + docs/codebase sections + TODO + freshness |
| `/cache-freshness-check` | [`cache-freshness-check/SKILL.md`](cache-freshness-check/SKILL.md) | Structured staleness; EOD records **Resume branch** via `scripts/resume-branch.sh` |
| `/daily-standup-with-cache` | `.grok/prompts/daily-standup-with-cache.md` + skill | Default for dev/review sessions (cache + TODO + branch + CONCERNS + direction ask) |
| `/read-codebase` | `.grok/prompts/read-codebase.md` + skill | Onboarding or full cache refresh into `docs/codebase/` + repo memory |
| `/cache-efficient` | `.grok/skills/cache-efficient/SKILL.md` | Token-efficient / cache-first mode. Load INDEX + targeted only; short bullets, heavy citations. Use at session start or when cost matters. Default lean tone unless "go deep". Chain with `/load-project-cache-first` or `/daily-standup-with-cache`. |
| `/project-drift-guardian` | `.grok/skills/project-drift-guardian/SKILL.md` | Core "avoid drift at all costs" guardian. Requirements DB (or project DB extension), branch discipline, pre/post CI/deploy/DB drift checks (code/scope/schema/container/infra). Scripts for checks + ops. Ties to DO hosting, safe DB updates, CI gates, evals, model-schema-check, etc. Run on planning, branches, before any deploys or DB changes. |
| `/digitalocean-app-platform-docr-deploy` | `.grok/skills/digitalocean-app-platform-docr-deploy/SKILL.md` (expanded to full project DO skill) | Complete DigitalOcean hosting skill for droplet and/or App Platform. Includes CI deployment workflows (GitHub Actions with built-in drift gates), safe database updates/migrations (integrated with prod-db-maintenance + verification), hardened containers, token scoping, and mandatory drift checks via project-drift-guardian. Full procedures, one-liners, yaml examples, and no-drift enforcement. |

## Audit / review commands

| Slash command | Source | Use when |
|---------------|--------|----------|
| `/filament-panel-review` | `.grok/prompts/filament-panel-review.md` + skill | Audits on any of the Filament panels (Admin, Documents, Signature Requests, Users) (cache first) |
| `/model-schema-check` | `.grok/prompts/model-schema-check.md` + skill | Pre/post migration or suspected schema drift (test DB only) |
| `/schema-audit-agent` | `.grok/agents/schema-audit-agent.md` + skill | Read-only schema/migration deep dive |
| `/bug-hunter-agent` | `.grok/agents/bug-hunter-agent.md` + skill | Comprehensive bug/weakness hunt; fix or suggest; chains `bug-hunt*` |
| `/systematic-debugging` | [`systematic-debugging/SKILL.md`](systematic-debugging/SKILL.md) | Known failure: root cause before any fix |
| `/verification-before-completion` | [`verification-before-completion/SKILL.md`](verification-before-completion/SKILL.md) | Evidence before done/fixed/passing claims |
| `/grill-me` | [`grill-me/SKILL.md`](grill-me/SKILL.md) | Stress-test a plan before `/orchestrator` or implementation |
| `/cyber-security-essentials` | `.grok/agents/cyber-security-essentials.md` + skill | UK NCSC Cyber Essentials (five controls) for code/config/CI; chains `cyber-essentials-*` |
| `/security-audit-agent` | `.grok/agents/security-audit-agent.md` + skill | Auth, permissions, consent, secrets |
| `/test-safety-agent` | `.grok/agents/test-safety-agent.md` + skill | Enforce test DB target + safety |
| `/eval-maintenance-task` | `.grok/skills/eval/maintenance-task/SKILL.md` | Post-maintenance evals for production readiness (registry cleanup, DB imports, live listings freshness). Moves standards into the system (Stage 5/8 per /ai-engineering-maturity). Run after one-liners for auditable reports. |

## Specialist agents (via skills or Task subagent)

| Slash command | Source | Use when |
|---------------|--------|----------|
| `/laravel-expert-agent` | `.grok/agents/laravel-expert-agent.md` + skill | Laravel 12 + Filament 5 architecture/code |
| `/mysql-database-expert` | `.grok/agents/mysql-database-expert.md` + skill | MySQL queries, schema, Laravel Eloquent + Python bridge |
| `/test-specialist-agent` | `.grok/agents/test-specialist-agent.md` + skill | Write/improve tests; red-green TDD at confirmed seams |
| `/todo-specialist-agent` | `.grok/agents/todo-specialist-agent.md` + skill | Maintain TODO-*.md and project docs |
| `/readme-specialist` | `.grok/agents/readme-specialist.md` + skill | Polish README, guides, reference docs |
| `/branch-context-agent` | `.grok/agents/branch-context-agent.md` + skill | Align changes to branch intent + TODO |
| `/github-expert-agent` | `.grok/agents/github-expert.md` + skill | GitHub Actions, workflows, PR hygiene, secrets |

## Guardrails & runtime

| Slash command | Source | Use when |
|---------------|--------|----------|
| `/github-branch-hygiene` | [`github-branch-hygiene/SKILL.md`](github-branch-hygiene/SKILL.md) | Report-only prune of merged remotes; `--apply` only after the user asks. Never deletes master/develop/staging/production |
| `/git-workflow-guardrails` | `.grok/skills/git-workflow-guardrails/SKILL.md` (full from .github/skills/) | Safe commit/push with security checklist + tests; branch promotion; tagging |
| `/ddev-local-runtime` | `.grok/skills/ddev-local-runtime/SKILL.md` (full from .github/skills/) | Enforce DDEV for all php/artisan/composer/pest/python/mysql/node cmds |
| `/digitalocean-app-platform-docr-deploy` | `.grok/skills/digitalocean-app-platform-docr-deploy/SKILL.md` (full project DO hosting skill) | Droplet and/or App Platform hosting, CI deployment (GitHub Actions with drift gates), safe database updates, hardening, token scopes, integrated /project-drift-guardian + schema checks + evals. Full procedures, examples, and no-drift enforcement. |
| `/amazon-ses-email` | `.grok/skills/amazon-ses-email/SKILL.md` (new for project) | Amazon SES setup for domain (sending + receiving emails). Non-Microsoft (AWS). Domain verification (DKIM/SPF/DMARC/MX), IAM, Laravel config, inbound processing (S3/SNS + webhook). Integrated with drift-guardian, security-audit, DO hosting, cache-first. One-liners + tests. |
| `/aws-route53-dns` | `.grok/skills/aws-route53-dns/SKILL.md` (new) | AWS Route 53 for project domains (hosted zones + delegation) + email DNS (verification TXT, DKIM CNAMEs, SPF, DMARC, MX for SES). Programmatic record management via change-resource-record-sets (UPSERT). Complements /amazon-ses-email (run SES verify first, then this for DNS). Non-Microsoft AWS. Guardian-enforced, IAM least-priv, dig verification, exports as code. |
| `/paypal-billing-integration` | `.grok/skills/paypal-billing-integration/SKILL.md` (new for project) | PayPal for payments + generating billing documents (invoices/receipts) at PayPal (non-Microsoft). Checkout, webhooks (payment/invoice events), Invoicing API, Filament billing views. Ties to SES for notifications, DO for hosting, drift-guardian for no-drift. Sandbox/live, security (webhook verification). |
| `/didit-identity-integration` | `.grok/skills/didit-identity-integration/SKILL.md` | Didit KYC/KYB/AML/biometrics. Canonical ref + export prompt. Sessions + SDK, webhook V2 sig. |
| `/loqate-address-integration` | `.grok/skills/loqate-address-integration/SKILL.md` | Loqate Address Capture (Find + Retrieve). Backend proxy, type-ahead UX. Signer/checkout addresses. Canonical ref + export. |
| `/project-drift-guardian` | `.grok/skills/project-drift-guardian/SKILL.md` | Avoid drift at all costs. Requirements tracking, drift checks (code/schema/container/deploy/scope), gates for CI/DO/DB. Includes scripts for automated checks. Use before planning, branches, deploys, or DB updates. |

## AI Engineering Maturity & Tooling Evolution

| Slash command | Source | Use when |
|---------------|--------|----------|
| `/ai-engineering-maturity` | `.grok/skills/ai-engineering-maturity/SKILL.md` | Assess and advance the project's (and team's) position on the 8 stages of AI engineering maturity (shared context, governance before scale, evals as product, AI as amplifier of good practices). Mandatory context when adding/extending skills, agents, prompts, MCP usage, or agentic workflows. |

## Efficiency / Caching (new)
- `/cache-efficient`: enforces minimal-token, cache-first responses. Integrated with existing load/daily-standup + INDEX + docs/codebase/. See the SKILL.md for load discipline (INDEX ≤3 + targeted sections only) and response format (≤120 words bullets + citations + "Next" actions). Now part of core session start flow.

## Maintenance

- Native Grok sources (full adapted content, no shortcuts): `.grok/prompts/*.md`, `.grok/agents/*.md`, `.grok/skills/*/SKILL.md`
- `.github/` versions kept for Copilot compatibility only.
- When source changes, keep the .grok/ versions updated as the primary for Grok (full instructions embedded).
- Commit these together with feature work.
- Also see `.grok/README.md` and `.grok/memories/INDEX.md`

## How created

All .grok/prompts/, .grok/agents/, .grok/skills/ (and caching) created new with **full content embedded** (no thin "read the .github original" shortcuts) on `feat/grok-prompts-agents-skills-from-github` directly from content in this repo's `the prior scaffolding source (adapted for project)` folder. 

Caching repo and memories fully implemented (symlinks + INDEX + stubs + docs/codebase/ skeleton).

"DO NOT shortcut to originals" followed — everything is self-contained native .grok files inside the project project folder.

## Discovery

Grok scans `.grok/skills/*/SKILL.md` (project) + `~/.grok/skills/` (user). Canonical list: [`registry.yaml`](registry.yaml). Verify: `python3 scripts/check_name_alignment.py`.

## Third-party authors

`/find-skills`, `/grill-me`, `/teach`, `/test-specialist-agent` (TDD fold), `/systematic-debugging`, `/verification-before-completion`, and the Vercel tables in `/nextjs-expert` + `/frontend-web-design-expert` are **adapted** from community skills (MIT). Credit: **Vercel Labs**, **Matt Pocock**, **Jesse Vincent** and **Prime Radiant** (obra/superpowers). See [`docs/reference/third-party-skills.md`](../../docs/reference/third-party-skills.md) and root `NOTICE`.
