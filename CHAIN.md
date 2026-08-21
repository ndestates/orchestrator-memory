# Chain Registry

**Cache is king.** Chains load shared cache **once** at the start, then pass minimal handoffs between steps — never reload full cache per step unless a step explicitly requires new files.

Machine-readable catalog (skills + chains): [`chains/registry.yaml`](chains/registry.yaml)

## Purpose

`/chain` discovers which skills and prompts work together for a task, runs them in order, and keeps token use lean via shared context and the handoff schema in `chain_policy` (manifest).

**Chains are optional.** When intent is ambiguous or the user prefers not to chain, the agent offers a menu with a **No chain** option and runs a single skill or direct task instead.

## Active chains

| Chain | Steps | Token tier | Use when |
|-------|-------|------------|----------|
| [session-start](chains/registry.yaml) | remote_last → check+card → envelope → security → lean cache → compound | low | **New day / after eod** — not same-day mid-day return |
| [session-resume](chains/registry.yaml) | prior session Branch (session-end card) → lean security → work | low | **Same-day return** after `/chain session-end` — not remote_last |
| [always-on-memory](chains/registry.yaml) | ingest → consolidate → query (full model catalog + agent roster); session brief | low | `/chain always-on-memory` or `memory_agent.py serve` |
| [wiki-ingest](chains/registry.yaml) | load-cache → llm-wiki ingest (raw → wiki pages + index/log; approval for writes) | low | Ingest one source into LLM wiki |
| [wiki-query](chains/registry.yaml) | load-cache → llm-wiki query (index-first; optional file-back) | low | Ask the compounding wiki |
| [wiki-lint](chains/registry.yaml) | load-cache → llm-wiki lint (report-only health) | low | Wiki contradictions / orphans / stale |
| [wiki-lint-watch](chains/registry.yaml) | llm-wiki host lint → loop-verifier (L1 manual) | low | Weekly-style wiki health watch |

| [token-monitor](chains/registry.yaml) | token-usage-meter (sync + report) | low | Token usage and context warnings |
| [loop-daily](chains/registry.yaml) | loop-triage → loop-verifier | low | Scheduled / manual L1 triage |
| [cache-freshness-watch](chains/registry.yaml) | cache-freshness-check → loop-verifier | low | Weekly cache staleness (Mon) |
| [chain-health-watch](chains/registry.yaml) | loop-engineering → loop-verifier | low | Weekly chain registry audit (Mon) |
| [github-ci-watch](chains/registry.yaml) | github-workflow-expert → loop-verifier | low | Weekly Actions health (Mon) |
| [repo-health-watch](chains/registry.yaml) | github-expert → git-workflow → loop-verifier | low | Weekly branch/PR hygiene (Mon) |
| [code-review](chains/registry.yaml) | code-review (process + stack + **existing strict skill**) → optional bug-hunter → security | low | Review the working diff — token-lean, report-only |
| [delivery](chains/registry.yaml) | branch-context → code-review (diff) → git-workflow → test-safety → tests | medium | Commit, push, PR |
| [push-secrets-guard](chains/registry.yaml) | github-expert → git-workflow (secrets/env hooks) | medium | Pre-push GitGuardian-safe guard; block `.env`/secrets/DB dumps |
| [promote-master](chains/registry.yaml) | branch-context → git gates → github PR sync → git promote | medium | Merge develop into master |
| [migration-safe](chains/registry.yaml) | model-schema-check → schema-audit → test-safety → engine → Laravel → Filament | medium | Migrations / schema work |
| [database-design](chains/registry.yaml) | data-architect → model-check → Laravel → engine → Filament | medium | ER design + Eloquent alignment |
| [laravel-database-design](chains/registry.yaml) | data-architect → model-check → Laravel → engine → Filament | high | Full Laravel + Filament DB design |
| [vector-db-assess](chains/registry.yaml) | load-cache → vector-db fit assessment | low | Should this project use vectors? |
| [vector-db-setup](chains/registry.yaml) | assess → data-architect → vector-db → Laravel → engine | medium | Vector store / RAG (after fit pass) |
| [security-flywheel](chains/registry.yaml) | find→triage→fix→ship→prevent | medium | `/chain security-flywheel` |
| [security-review](chains/registry.yaml) | security-audit → test-safety | medium | Auth, permissions, secrets |
| [cyber-essentials-review](chains/registry.yaml) | cyber-security-essentials → security-audit | medium | UK NCSC Cyber Essentials code/config |
| [cyber-essentials-hunt](chains/registry.yaml) | load-cache → CE → bug-hunt → security | high | CE compliance + defect hunt |
| [cyber-essentials-pre-deploy](chains/registry.yaml) | drift → CE → pre-deploy hunt → security → test-safety | high | CE readiness before release |
| [cyber-essentials-maturity](chains/registry.yaml) | CE → ai-maturity → security | medium | CE + engineering SDLC posture |
| [deploy-check](chains/registry.yaml) | drift → docker → workflows → github → git → DO → eval | high | Production deploy |
| [docker-deploy](chains/registry.yaml) | docker → workflows → github → git → DO | high | Hardened image + CI + registry |
| [deploy-dns-infra](chains/registry.yaml) | Route53 (app+DKIM) → DO firewall → SES → git | high | Production DNS + perimeter |
| [github-workflow-setup](chains/registry.yaml) | load-cache → github-expert → github-workflow → security → git | medium | Create/amend workflows and set secrets |
| [ci-branch-readiness](chains/registry.yaml) | load-cache → ci-readiness expert → github-expert → git-workflow | medium | Pre-push CI gate — branch vs workflows (per wave project) |
| [workflow-debug](chains/registry.yaml) | load-cache → github-workflow-expert (diagnose-failure) → github-expert → git-workflow-guardrails | medium | Debug failing workflows, analyze logs, root-cause + exact fixes to stop continual failures |
| [ses-email-setup](chains/registry.yaml) | route53-dns → amazon-ses | medium | Email DNS + SES (bootstrap) |
| [complex-task](chains/registry.yaml) | load-cache → orchestrator | high | Multi-domain features |
| [repo-health](chains/registry.yaml) | github-expert → git-workflow → drift-guardian | medium | Repo/branch health, pull all branches |
| [session-end](chains/registry.yaml) | checkpoint → **rich resume card** (`Source: session-end`) | low | **Mid-day pause**; next open = **`/chain session-resume`** |
| [eod-shutdown](chains/registry.yaml) | todo → changelog → readme → cleanup → vault + **rich card** | low | Day closed; next open = **`/chain session-start`** |
| [documentation-full](chains/registry.yaml) | load-cache → acquire-codebase-knowledge → readme-specialist → documentation-specialist | high | Full project documentation + optional cache rebuild |
| [documentation-refresh](chains/registry.yaml) | load-cache → readme-specialist → documentation-specialist | medium | Update docs from current cache (no full scan) |
| [research-deep-dive](chains/registry.yaml) | load-cache → research-deep-dive (frame → gather → memo) | medium | External-topic research memo before implementation (no default web) |
| [template-deploy](chains/registry.yaml) | load-cache → orchestrator-deploy | medium | Deploy .grok + root chains to target project |
| [loop-engineering-audit](chains/registry.yaml) | load-cache → loop-engineering | low | Loop maturity and readiness |
| [pre-flight](chains/registry.yaml) | branch-context → drift-guardian → test-safety | medium | Before starting feature work |
| [laravel-feature](chains/registry.yaml) | load-cache → branch → laravel-expert → tests | medium | Laravel/Filament implementation |
| [filament-review](chains/registry.yaml) | load-cache → filament-panel-review → security | medium | Filament panel audit |
| [paypal-setup](chains/registry.yaml) | drift-guardian → paypal-billing | medium | PayPal billing integration |
| [didit-identity-setup](chains/registry.yaml) | drift-guardian → didit-identity | medium | Didit KYC/KYB/AML |
| [loqate-address-setup](chains/registry.yaml) | drift-guardian → loqate-address | medium | Loqate Address Capture |
| [prod-db-ops](chains/registry.yaml) | drift-guardian → prod-db-maintenance → eval | high | Production DB maintenance |
| [cache-rebuild](chains/registry.yaml) | load-cache → acquire-codebase-knowledge | high | Full cache refresh (stack detection + seven docs) |
| [ai-maturity](chains/registry.yaml) | load-cache → ai-engineering-maturity | low | AI engineering maturity assessment |
| [web-design](chains/registry.yaml) | load-cache → web-build-design → Next/Astro/Nuxt/Go/Laravel expert | medium | Marketing/landing pages (multi-framework) |
| [beta-ready](chains/registry.yaml) | load-cache → beta-checklist → drift-guardian | medium | Pre-beta readiness |
| [bug-hunt](chains/registry.yaml) | load-cache → bug-hunter-agent (scan) | medium | Find bugs — report only |
| [bug-hunt-fix](chains/registry.yaml) | load-cache → bug-hunter (fix) → test-safety → tests | high | Hunt + safe fixes + verify |
| [bug-hunt-deep](chains/registry.yaml) | deep hunt → security → schema → test-safety → tests | high | Full defect pass (report) |
| [bug-hunt-fix-deep](chains/registry.yaml) | deep fix → security → test-safety → tests → schema | high | Fix + security + mandatory tests |
| [bug-hunt-pre-deploy](chains/registry.yaml) | drift → hunt → security → test-safety → schema | high | Pre-release report |
| [bug-hunt-pre-deploy-fix](chains/registry.yaml) | drift → hunt fix → security → test-safety → tests | high | Pre-release with safe fixes |

**Fix policy:** auto-fix low/medium isolated issues; critical/high and auth/payment/crypto are suggest-only unless you approve in args. **Rollback required** before fixes (`reports/bugs/backups/`); critical **security** fixes are exempt and kept on rollback.

**Skill catalog:** `chains/registry.yaml` also lists every skill (`skills:` section). `.grok/skills/` holds skill *content* only.

## Custom chains

When a user runs a **logical** multi-skill sequence not yet in the registry, `/chain` may **register** it after a successful run (Phase 5 in the chain skill):

1. Qualifies: logical order, resolvable invokes, reusable intent, within token budget, not duplicate.
2. Adds entry to `chains/registry.yaml` + row here.
3. Runs `bash scripts/chain-audit.sh`.

User can decline registration; one-off work stays with `/orchestrator`.

## Invocation

| Tool | Command |
|------|---------|
| Grok | **`/chain session-start`** (type in Grok command line) · or `/chain <id|intent>` |
| Claude Code | **`/chain session-start`** (type in Claude command line; `.claude/commands/chain.md`) |
| GitHub Copilot | `chain` skill (`.github/skills/chain/SKILL.md`) — same `/chain session-start` text |

## Opt-out (user choice)

| Situation | Behaviour |
|-----------|-----------|
| User says "no chain", "skip chain", "just run X" | Run single skill or direct task — no multi-step chain |
| Ambiguous intent or `/chain` with no args | Show top 2 chains **plus** "No chain" — wait for reply |
| Low-confidence match | Confirm: `Run chain <id>? yes / no / other skill` |

## Handoff rules (token-efficient)

1. **One cache load** per chain — cite files once in the chain header.
2. **≤80 tokens** per step handoff (bullets or compact JSON).
3. **No source reads** until a step in the chain requires them.
4. **Skip optional steps** when `when` conditions are false (e.g. `code_changed: false`).
5. End with **Chain summary**: steps run, skipped, cache cited, next action.

## Adding a chain

**Manual:** edit `chains/registry.yaml` + this table + `chain-audit.sh`.

**Automatic:** `/chain` Phase 5 after a successful custom run (see Custom chains above).

Always: `bash scripts/chain-audit.sh` then `python3 scripts/sync_grok_to_github_claude.py` if skills changed.

## Related

- Loops (scheduled autonomy): `LOOP.md`, `/loop-engineering`
- Single-step cache mode: `/cache-efficient`
- Ad-hoc multi-agent plans: `/orchestrator`