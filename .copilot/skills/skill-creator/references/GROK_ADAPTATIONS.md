# Grok / Orchestrator Adaptations

This skill was ported from the Anthropic skills repo (reports/research/ports/skill-creator).

## Key Differences from Original

- **Execution model**: Uses `spawn_subagent` (with capability_mode and optional worktree isolation) instead of Claude Code subagents or `claude -p`.
- **Model**: Grok (via host TUI/agent). Grader can use stronger effort if supported. No direct `claude -p`.
- **Cache discipline (mandatory)**: Every major step starts with manifest + `/load-project-cache-first` or equivalent. Lean mode by default.
- **Workspace**: `reports/skill-dev/<skill>/iteration-N/...` (not sibling workspace).
- **Token / cost awareness**: Integrated with `token-usage-meter`. High cost activity — gate per `loop-budget.md` and explicit approval for full cycles.
- **Description optimization**: Adapt `run_loop` / `improve_description` to use subagent self-calls or emit prompts for the user. Train/test split still valuable.
- **Viewer**: Prefer `--static <path.html>` output (no browser assumption in headless/CI).
- **No Claude-specific**: Remove Anthropic SDK deps for core path. MCP eval harness (separate) is optional.
- **Schemas**: Keep exact field names where viewer/agg depend on them (e.g. grading `text`/`passed`/`evidence`).

## How to Run Evals (Current Skeleton)

1. Use spawn_subagent for with-skill vs baseline.
2. Capture timing/tokens from subagent results.
3. Use grader prompt from `references/agents/grader.md`.
4. Aggregate manually or with copied `scripts/aggregate_benchmark.py` (will need minor Grok tweaks for paths/models).
5. Generate static review with `eval-viewer/generate_review.py --static ...`

## Future Ports

See `reports/research/skill-port-plan.md` for phased plan:
- Phase 2+: native grader harness, full parallel run_skill_eval using spawn_subagent.
- Description loop adaptation.
- MCP quality skill + harness.
- Integration with create-skill, loop-engineering, chains.

## Other Models (from same source)

- Themes copied to `references/themes/` (can be promoted to web-build-design/assets).
- webapp-testing and frontend-design patterns available in ports for future merge into test-specialist or web-build-design.

## References

- Original source: reports/research/ports/skill-creator/
- Project plan: reports/research/skill-port-plan.md
- Project token policy + loop-budget.md

Keep SKILL.md lean; delegate details here.
