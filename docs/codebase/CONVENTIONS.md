# Conventions

[UPDATED 2026-07-07] — aligned to full docs site update; cross-links to human daily-workflow and delivery guides.

## Session Conventions

- **Manifest first:** read `.github/project-manifest.yaml` (or `.claude/` copy) before deep work.
- **Cache first:** load `docs/codebase/` + latest TODO before source trees.
- **Lean tokens:** cite cache by section; ≤120 words default (`/cache-efficient`). `max_cache_files_default: 2` extra files after spine.
- **Grep before read:** `token_policy.grep_before_read: true` — grep headings/use offset+limit before full reads.
- **No source until confirmed:** `no_source_until_confirmed: true`.
- **Exact agent names** when delegating (match `.claude/agents/` / `.github/agents/` filenames).
- **Script-first execution:** multi-line or quoted logic → write `scripts/*.py|sh` or `/tmp/agent-*`; run `python3 scripts/foo.py` / `bash scripts/foo.sh`. See `/script-not-shell` and CONCERNS §6.

## Branch Conventions

- `feature/*` → PR → `develop` → PR → `master`
- Do not force-push protected branches.
- Local commits to `develop`/`master` require PR (branch protection).
- Working-branch naming: `feature/work-YYYY-MM-DD`, `feature/<topic>-YYYY-MM-DD`.

See human docs: guides/daily-workflow.md and operations/delivery.md for end-to-end procedures.

## Chain Conventions

- Chains are **optional** — offer "No chain" on ambiguity (`chain_policy.allow_opt_out`).
- One shared cache load per chain; ≤80-token handoffs between steps.
- `require_confirm_before_run: true`; `max_steps_default: 6`.
- `scheduled_allowlist` chains skip confirm when invoked with explicit id + `scheduled` (or `CHAIN_SCHEDULED=1`).
- After successful `/chain`, run `bash scripts/chain-completion-write.sh` to update `STATE.md` + `loop-run-log.md`.
- Register new chains in `chains/registry.yaml` + `CHAIN.md`; run `chain-audit.sh` (custom chains require audit).

## Loop Conventions

- L1 = report-only; no auto-fix, no source reads (`loop_policy.allow_l2: false`).
- Update `STATE.md` + `loop-run-log.md` every triage run and after chain completion.
- Verifier judges artifacts only — not maker reasoning.
- Each pattern declares required cache files (`patterns/registry.yaml`); cap `max_cache_files_per_loop: 2`.

## TODO Conventions

- File naming: `TODO/YYYY-MM-DD_TODO.md`; latest by date wins.

## Efficiency & Provider Prompt Caching

When making direct calls to LLM providers (outside the orchestrator's own cache system):

- **Anthropic**: Use `cache_control={"type": "ephemeral"}` on system prompts, long documents, and tool schemas. See `reports/research/anthropic-prompt-caching.py` and `claude_usage_guide.md`.
- **xAI/Grok**: Relies on automatic prefix caching. Use consistent `prompt_cache_key` or headers for best results. Reference: `token-usage-meter/references/xai-prompt-caching.md`.
- **Gemini**: Use the Context Caching API for large static content.
- **Copilot / OpenAI-based**: Use whatever context management the backend supports (no direct equivalent to Anthropic ephemeral cache in all cases). Prefer sending stable prefixes once per conversation.

**General rules**
- Cache the largest, most stable prefixes first.
- Always log the full `usage` object (cache hits vs creation).
- Combine with orchestrator practices: `docs/codebase/`, lean token policy, `load-project-cache-first`.
- See multi-AI best practices (`multi-ai-best-practices-setup.md`) and prompt patterns.
- Carry forward open items (note **Carried from:** + branch); mark done with `[x]`.
- Sync with `STATE.md` open queue where overlap exists.
- Topic TODOs allowed: `TODO/YYYY-MM-DD_<topic>_TODO.md`.

## Sync & Deploy Conventions

- Edit `.grok/` skills first (source of truth); add to `chains/registry.yaml` (`skills:` section) + README; run `python3 scripts/sync_grok_to_github_claude.py` before PR (mirrors to `.github/`, `.copilot/`, `.claude/`).
- Keep `.github/project-manifest.yaml` and `.claude/project-manifest.yaml` in sync.
- Template → app repos via `scripts/deploy_grok_to_project.py` (bundles) or `scripts/deploy-*-wave.sh` (fleet); apply stack overrides from `scripts/stack-profiles/`.

## CI / Commit Conventions

- Conventional-commit prefixes in history: `feat`, `fix`, `chore`, `docs` (often scoped, e.g. `feat(orchestrator):`, `chore(todo):`).
- GitHub Actions pinned to Node 24 (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`, `verify_github_actions_node24.py`); `actions/checkout@v6`, `upload-artifact@v7`.

## Evidence

- `.claude/project-manifest.yaml` (`token_policy`, `loop_policy`, `chain_policy`, `agent_policy`)
- `CHAIN.md`, `LOOP.md`, `loop-budget.md`, `patterns/registry.yaml`
- `git log` (commit-prefix patterns), `.github/workflows/*.yml` (Node 24 env)
- `TODO/2026-06-21_TODO.md` (carry-forward format)
