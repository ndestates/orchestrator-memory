# Orchestrator Template Cache Index

[UPDATED 2026-07-15] — LLM Wiki Phase 1 scaffold (`wiki/`, `/llm-wiki`, mode lean); prior: Phase 0 policy, vault graph / multi-AI.

**Human documentation:** [docs/index.md](../index.md) — navigable guides, reference, and operations (full site update 2026-07-07; see guides/knowledge-vault.md for the secure self-building vault graph, guides/daily-workflow.md, reference/manifest.md, operations/delivery.md, etc.).

This repository is a **project-agnostic orchestrator template** for manifest-first, cache-first AI-assisted delivery. It is not an application codebase — it ships prompts, agents, skills, loops, and chains.

## Project Snapshot

- **Name:** Project Template (`ndestates/orchestrator`)
- **Goal:** Reusable flow from repo setup → beta readiness in one day
- **Default branch:** `master`
- **Promotion:** `feature/*` → `develop` → `master`
- **Stack:** generic (manifest-driven)
- **Token mode:** lean
- **Source of truth:** `.github/project-manifest.yaml`

## What This Repository Contains

| Area | Path | Purpose |
|------|------|---------|
| Grok native | `.grok/skills/`, `.grok/prompts/`, `.grok/agents/` | Primary skill/prompt sources |
| Copilot | `.github/skills/`, `.github/prompts/`, `.github/agents/` | Synced from `.grok/` |
| Claude Code | `.claude/commands/`, `.claude/agents/` | Synced from `.grok/` |
| Sync script | `scripts/sync_grok_to_github_claude.py` | Propagate `.grok/` → `.github/` + `.claude/` |
| Loops | `LOOP.md`, `patterns/`, `STATE.md` | Scheduled L1 autonomy (daily + 4 weekly watches + branch-promotion) |
| Chains | `CHAIN.md`, `chains/registry.yaml` | On-demand skill composition (`/chain`) |
| Multi-AI support | `.gemini/`, `.grok/prompts/multi-ai-best-practices-setup.md`, `reports/research/claude_best_practices.md`, `claude_usage_guide.md`, `grok_usage_guide.md`, `who-i-am-profile-template.md`, rollout-plan | Cross-platform best practices (Grok/Claude/Copilot/Gemini). Source research in claude_* files; Grok adaptation in grok_usage_guide.md. Persistent context via memories + cache, "who I am", sparring, efficiency, meta-prompting, tools/MCP. Also covers direct SDK prompt caching for Anthropic (see claude_usage_guide.md). |
| MCP server | `mcp-server/` | Cache-first read-only MCP tools (dev-only) |
| Deploy | `scripts/deploy_grok_to_project.py`, `scripts/wave-*.sh`, `scripts/stack-profiles/` | Template → app repos (single + fleet) |
| Cache docs | `docs/codebase/` | Lean session startup (this folder) |
| TODO | `TODO/` | Daily coordination |
| Reports | `reports/loops/`, `reports/chains/`, `reports/vault/` | Triage, chain artifacts, **secure self-building vault graph ledger** (hash-chained events; see human guide knowledge-vault.md) |
| CI | `.github/workflows/` | Release, sync, loop triage, branch promotion |

## Cache Files

| File | Contents | Human cross-link |
|------|----------|------------------|
| `ARCHITECTURE.md` | Manifest → cache → orchestrator / chains / loops flow + vault graph | getting-started/project-overview.md, guides/knowledge-vault.md, reference/manifest.md |
| `STRUCTURE.md` | Directory map | getting-started/project-overview.md, reference/index.md |
| `STACK.md` | Tooling and runtime assumptions | reference/manifest.md, guides/knowledge-vault.md |
| `CONVENTIONS.md` | Branch rules, token discipline, naming | guides/daily-workflow.md, operations/delivery.md |
| `INTEGRATIONS.md` | GitHub Actions, gh CLI, sync targets | guides/template-deploy.md, guides/wave-deploy-log.md |
| `TESTING.md` | Audit scripts and validation gates | operations/testing.md |
| `CONCERNS.md` | Open risks (numbered) — incl. MCP surface, wave blast radius, vault security | guides/knowledge-vault.md, operations/testing.md, reference/manifest.md |
| `SECTIONS.md` | Heading index — grep then section Read only (`scripts/generate-cache-sections.py`) | — |
| `.codebase-freshness.txt` | Lean spine: scan date + stack summary (≤35 lines; cache-efficient / standup) | — |
| `reports/vault/events.jsonl` | Secure vault graph (content-hashed lessons + provenance; verified on compound) | guides/knowledge-vault.md |
| `reports/research/llm-wiki-karpathy-plan.md` | LLM Wiki (Karpathy) product plan | reference/manifest.md · `wiki/` |
| `wiki/index.md` | LLM-maintained knowledge catalog (Phase 1; mode lean) | plan + `/llm-wiki` |
| `.codebase-scan.txt` | Full scan artifact from `/read-codebase` — do not load in lean sessions | — |

## Session Entry Points

| Command | When |
|---------|------|
| `/load-project-cache-first` | Every session — master cache loader |
| `/chain session-start` | Cache → standup → lean mode (optional chain) |
| [Installation](../getting-started/installation.md) | Bootstrap + per-app `orchestrator init/upgrade` (not fleet wave) |
| [Licensing](../reference/licensing.md) | Optional license gate for init/upgrade |
| `/daily-standup-with-cache` | Daily dev/review opener |
| `/chain loop-daily` | L1 triage + verifier |
| `/chain repo-health-watch scheduled` | Weekly branch/PR hygiene (Mon; allowlisted) |
| `bash scripts/chain-completion-write.sh` | After `/chain` — update STATE + loop-run-log |
| `/orchestrator` | Multi-domain ad-hoc planning |
| `/read-codebase` | Full cache refresh (rare) |
| `/script-not-shell` | Write script files instead of inline shell (CONCERNS §6) |
| `/documentation-specialist` | Full project docs via chain composition |
| `/chain documentation-full` | load-cache → read-codebase → readme → documentation-specialist |
| Skill + chain catalog | `chains/registry.yaml` — register new skills in `skills:` section; `.grok/skills/README.md` for human index |

## How To Use This Cache

1. Read this file first.
2. Read `CONCERNS.md` and latest `TODO/*.md`.
3. Load only additional cache files needed for the task.
4. Use source trees only after cache context is sufficient.
5. Re-sync after `.grok/` skill/prompt changes: `python3 scripts/sync_grok_to_github_claude.py`
6. For cross-platform AI best practices: load `reports/research/claude_best_practices.md` + `claude_usage_guide.md` (source) + `grok_usage_guide.md` (Grok version) + `who-i-am-profile-template.md`. Invoke `.grok/prompts/multi-ai-best-practices-setup.md`. Use `.gemini/` for Gemini. See rollout plan. Start with `/chain session-start` + cache.
   - For direct Anthropic SDK calls with prompt caching, see `claude_usage_guide.md` → "Direct SDK Usage: Anthropic Prompt Caching" (system prompts, tools, and long documents).