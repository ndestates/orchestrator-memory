# Grok commands for Project Template (orchestrator)

**Project**: Reusable orchestrator template (`ndestates/orchestrator`) — manifest-first, cache-first AI-assisted delivery. Ships prompts, agents, skills, loops, and chains; not an application codebase. Read **`.grok/project-manifest.yaml`** for stack and paths (synced from `.github/project-manifest.yaml`).

Project-scoped skills and agents mirror [`.github/`](../.github/) (prompts, agents, and guardrails). Use them as slash commands in Grok Build / Grok CLI (`/skill-name` or `/skills <name>`).

## Caching and Memories (Implemented)

- Repo cache: `.grok/memories/repo/` (symlinked to `.copilot/memories/repo/`)
- Session memories: `.grok/memories/session/`
- INDEX: [`.grok/memories/INDEX.md`](memories/INDEX.md) — always read first; load ≤3 + core
- Canonical cache also in `docs/codebase/` (README.md + sections) + `.copilot/memories/`

Use `/load-project-cache-first` or `/daily-standup-with-cache` at start of sessions.

**Native .grok sources** (full content, no external shortcuts):
- Prompts: `.grok/prompts/*.md`
- Agents: `.grok/agents/*.md`
- Skills: `.grok/skills/*/SKILL.md`

`.github/`, `.copilot/skills/`, and `.claude/` versions are synced from `.grok/` via `scripts/sync_grok_to_github_claude.py` for Copilot and Claude Code compatibility.

## Session start (recommended order)

**One-time:** `bash scripts/setup-who-i-am.sh` → edit `.grok/memories/who-i-am.md` (see `docs/getting-started/who-i-am-setup.md`).

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/load-project-cache-first` | `.grok/prompts/load-project-cache-first.md` (and skill) | Master cache loader (docs/codebase + TODO + CONCERNS + memories + who-i-am) |
| `/daily-standup-with-cache` | `.grok/prompts/daily-standup-with-cache.md` (and skill) | Recommended daily start (cache + TODO + branch + synthesis) |
| `/read-codebase` | `.grok/prompts/read-codebase.md` (and skill) | Full scan + refresh `docs/codebase/` + repo memory (use rarely) |

## Documentation

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/documentation-specialist` | `.grok/skills/documentation-specialist/SKILL.md` | Full project docs; chains load-cache + read-codebase + readme-specialist |
| `/chain documentation-full` | `chains/registry.yaml` | Full doc pipeline with optional codebase scan |
| `/chain documentation-refresh` | `chains/registry.yaml` | Doc update from current cache |

## Script discipline (orchestrator)

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/script-not-shell` | `.grok/skills/script-not-shell/SKILL.md` | Avoid inline shell escaping — write temp (`/tmp/agent-*`) or permanent (`scripts/`) files first (CONCERNS §6) |

## Loop engineering (cache is king)

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/loop-triage` | `.grok/skills/loop-triage/SKILL.md` | L1 daily triage — cache-first, report to `reports/loops/` + `STATE.md` |
| `/loop-verifier` | `.grok/skills/loop-verifier/SKILL.md` + agent | Checker: validates artifacts, not maker reasoning |
| `/loop-engineering` | `.grok/skills/loop-engineering/SKILL.md` | Patterns, maturity, `scripts/loop-audit.sh` |

Registry: `LOOP.md` · Schedule: `.github/workflows/loop-daily-triage.yml` · **Cache is king** on every run.

## Skill chains (on-demand composition)

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/chain` | `.grok/skills/chain/SKILL.md` | Auto-match intent → run skill/prompt chain from `chains/registry.yaml` with one shared cache load |

Registry: `CHAIN.md` · Audit: `scripts/chain-audit.sh` · **Cache is king** — load once, hand off minimally between steps.

## End of day

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/ddev-cleanup` | `.grok/skills/ddev-cleanup/SKILL.md` | Drift check, ddev stop (app repos), TODO/cache, commit + push |

Suggested EOD chain: `/chain` with `todo-specialist` → `readme-specialist` → `ddev-cleanup`.

## Reviews and audits

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/filament-panel-review` | `.grok/prompts/filament-panel-review.md` + skill | Filament panel/resource review with cache (Laravel app repos) |
| `/cache-efficient` | `.grok/skills/cache-efficient/SKILL.md` | Token-efficient cache-first mode. Load INDEX + targeted only; short bullets + citations; ≤120 words default. |
| `/model-schema-check` | `.grok/prompts/model-schema-check.md` + skill | Model/DB schema drift check (test DB only) |
| `/schema-audit-agent` | `.grok/agents/schema-audit-agent.md` + skill | Schema / migration audit |
| `/security-audit-agent` | `.grok/agents/security-audit-agent.md` + skill | Security, permissions, auth |
| `/test-safety-agent` | `.grok/agents/test-safety-agent.md` + skill | Test DB safety (target `test` only) |

## Specialists

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/laravel-expert-agent` | `.grok/agents/laravel-expert-agent.md` + skill | Laravel + Filament (forked app repos; read manifest for stack) |
| `/mysql-database-expert` | `.grok/agents/mysql-database-expert.md` + skill | MySQL + Eloquent + Python DB |
| `/test-specialist-agent` | `.grok/agents/test-specialist-agent.md` + skill | Pest / test code |
| `/todo-specialist-agent` | `.grok/agents/todo-specialist-agent.md` + skill | TODO maintenance |
| `/readme-specialist` | `.grok/agents/readme-specialist.md` + skill | README / docs |
| `/branch-context-agent` | `.grok/agents/branch-context-agent.md` + skill | Branch vs TODO alignment |
| `/github-expert-agent` | `.grok/agents/github-expert.md` + skill | GitHub workflows, Actions, PRs |

## Repository & runtime guardrails

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/git-workflow-guardrails` | `.grok/skills/git-workflow-guardrails/SKILL.md` | Commit/push/PR/tag with security + tests |
| `/ddev-local-runtime` | `.grok/skills/ddev-local-runtime/SKILL.md` | Enforce DDEV for app repos (`environment_manager: ddev`) |
| `/digitalocean-app-platform-docr-deploy` | `.grok/skills/digitalocean-app-platform-docr-deploy/SKILL.md` | DO hosting, CI, DB updates, drift gates |
| `/amazon-ses-email` | `.grok/skills/amazon-ses-email/SKILL.md` | Amazon SES for target app domain (send + receive) |
| `/aws-route53-dns` | `.grok/skills/aws-route53-dns/SKILL.md` | Route 53 DNS + email records for target domains |
| `/paypal-billing-integration` | `.grok/skills/paypal-billing-integration/SKILL.md` | PayPal payments + billing docs for target apps |
| `/web-build-design` | `.grok/skills/web-build-design/SKILL.md` | SaaS marketing + design (Laravel/Livewire app repos) |

## Tools and MCP

Grok uses MCP for tools (see `.grok/config.toml`, mcp-server/README.md). Tools include cache reads, TODO, chains, audits. Enable via config for full tool calling in Grok Build.

## AI Engineering Maturity

| Grok command | Source | Purpose |
|--------------|--------|---------|
| `/ai-engineering-maturity` | `.grok/skills/ai-engineering-maturity/SKILL.md` | 8 stages of AI engineering maturity (team/org view). Assess skills/agents/MCP adoption; avoid drift/islands. |

## Multi-AI Best Practices (Grok/Claude/Copilot/Gemini)

See:
- `.grok/prompts/multi-ai-best-practices-setup.md` (core reusable setup prompt)
- `reports/research/claude_best_practices.md` and `claude_usage_guide.md` (source distillation of high-signal Claude workflows from the Anatoli thread)
- `reports/research/grok_usage_guide.md` (Grok-optimized adaptation created for this project)
- `reports/research/who-i-am-profile-template.md` (shared profile for persistent context across platforms)
- Rollout plan: `reports/research/multi-ai-best-practices-rollout-plan.md`

Key ideas: persistent context via `.grok/memories/` + cache load, detailed "who I am", thinking partner mindset (ask questions first, sparring), efficiency (specify length + no preambles), meta-prompting, style cloning, tool/MCP use.

Gemini support added via `.gemini/` (Gems + instructions). Always load the research files + multi-ai prompt when working on AI workflows or self-improving the orchestrator's own usage patterns.

## Subagents (via Task tool)

Specialized agents live in [`.grok/agents/`](agents/). Spawn via `spawn_subagent` (or Task in some contexts) with `subagent_type` or persona; the .md files seed the prompt.

## Authoritative rules

- Runtime / security / manifest / data safety: [`.grok/skills/copilot-instructions/SKILL.md`](skills/copilot-instructions/SKILL.md) (mirrored to `.github/copilot-instructions.md`)
- Loaded via root AGENTS.md or project rules if present.

## Bundled Grok skills

Global: `/implement`, `/review`, `/design`, `/execute-plan`, `/pr-babysit`, `/check-work`, `/best-of-n` etc. (see /skills)

---

Orchestrator template `.grok/` tree. Sync to `.github/` and `.claude/` via `scripts/sync_grok_to_github_claude.py`. Wave deploy customizes skills per target app via `scripts/customize-skills-for-project.py`.