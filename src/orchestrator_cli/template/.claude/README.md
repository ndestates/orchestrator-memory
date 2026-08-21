# .claude/ — Claude Code Native Configuration

This directory mirrors the orchestrator/agent system under `.github/` and `.grok/` but uses Claude Code's native conventions. Content is synced from `.grok/` via `scripts/sync_grok_to_github_claude.py`.

## Layout

```
.claude/
├── project-manifest.yaml      # Source of truth for stack, paths, token policy
├── agents/                    # Subagents (invoked via Task tool or auto-routing)
│   ├── orchestrator.md
│   ├── todo-specialist.md
│   ├── schema-audit.md
│   ├── security-audit.md
│   ├── test-safety.md
│   ├── test-specialist.md
│   ├── laravel-expert.md
│   ├── python-expert.md
│   ├── frontend-expert.md
│   ├── mysql-database-expert.md
│   ├── github-expert.md
│   ├── branch-context.md
│   └── readme-specialist.md
└── commands/                  # Slash commands (synced from .grok/skills + .grok/prompts)
    ├── orchestrator.md        → /orchestrator
    ├── multi-faceted.md       → /multi-faceted
    ├── load-cache.md          → /load-cache
    ├── daily-standup.md       → /daily-standup
    ├── read-codebase.md       → /read-codebase
    ├── cache-efficient.md     → /cache-efficient
    ├── chain.md               → /chain
    ├── loop-triage.md         → /loop-triage
    ├── loop-verifier.md       → /loop-verifier
    ├── loop-engineering.md    → /loop-engineering
    ├── security-audit.md      → /security-audit
    ├── model-schema-check.md  → /model-schema-check
    ├── filament-panel-review.md → /filament-panel-review
    ├── git-workflow-guardrails.md → /git-workflow-guardrails
    ├── ddev-local-runtime.md  → /ddev-local-runtime
    ├── project-drift-guardian.md → /project-drift-guardian
    ├── digitalocean-deploy.md → /digitalocean-deploy
    ├── prod-db-maintenance.md → /prod-db-maintenance
    ├── eval-maintenance-task.md → /eval-maintenance-task
    ├── ai-engineering-maturity.md → /ai-engineering-maturity
    ├── amazon-ses-email.md    → /amazon-ses-email
    ├── amazon-ses-setup.md    → /amazon-ses-setup
    ├── aws-route53-dns.md     → /aws-route53-dns
    ├── aws-route53-dns-setup.md → /aws-route53-dns-setup
    ├── paypal-billing.md      → /paypal-billing
    ├── paypal-integration.md  → /paypal-integration
    ├── web-build-design.md    → /web-build-design
    ├── laravel-expert.md      → /laravel-expert
    ├── mysql-database-expert.md → /mysql-database-expert
    ├── test-specialist.md     → /test-specialist
    ├── todo-specialist.md     → /todo-specialist
    ├── readme-specialist.md   → /readme-specialist
    ├── branch-context.md      → /branch-context
    ├── github-expert.md       → /github-expert
    ├── schema-audit.md        → /schema-audit
    └── test-safety.md         → /test-safety
```

Top-level instructions live in `CLAUDE.md` at the repo root (auto-loaded by Claude Code).

## MCP (develop-only)

1. `bash scripts/ensure-mcp-host.sh`
2. Merge `.claude/mcp.claude.example.json` into Claude Desktop / Claude Code MCP settings (or use `mcp-server/config/mcp.claude.example.json`).
3. For DDEV app repos: `mcp-server/config/mcp.claude.ddev.example.json` + `Dockerfile.mcp`.

Launcher: `scripts/mcp-host-stdio.sh` (auto-repairs venv). See `docs/reference/tools/multi-platform-tool-use.md`.

## Key Differences vs `.github/` version

| `.github/` | `.claude/` |
|---|---|
| `AGENTS.md` (descriptive index) | `CLAUDE.md` (auto-loaded instructions) |
| `agents/*.agent.md` | `agents/*.md` with YAML frontmatter (Claude Code subagents) |
| `prompts/*.prompt.md` + `skills/*/SKILL.md` | `commands/*.md` invoked as `/command-name` |
| VS Code Copilot | Native multi-subagent delegation via the Task tool |

## Subagent Invocation

Subagents are invoked automatically by Claude when their `description` matches the task, OR explicitly via the Task tool:

```
Use the orchestrator subagent to plan: <request>
```

The orchestrator dispatches to specialists (`laravel-expert`, `python-expert`, etc.). For multi-lane plans it dispatches independent lanes concurrently in a single message.

## Multi-Lane Parallel Execution

See `.claude/agents/orchestrator.md` for the Shape B schema (lanes + merge_gates). The orchestrator is the only entry point that produces multi-lane plans.

## Manifest Sync

`.claude/project-manifest.yaml` and `.github/project-manifest.yaml` should be kept in sync. The `.claude/` copy is canonical for Claude Code sessions; the `.github/` copy is canonical for VS Code Copilot sessions.

## Re-sync from Grok

When `.grok/skills/`, `.grok/prompts/`, or `.grok/agents/` change:

```bash
python3 scripts/sync_grok_to_github_claude.py
```

## Portability

1. Copy `.claude/` and `CLAUDE.md` to the target repo.
2. Edit `.claude/project-manifest.yaml` — set `project.name`, `stack.framework`, `stack.language`, `runtime.*`, and `paths.*`.
3. Optionally remove subagents/commands that don't apply.
4. Run `/read-codebase` once to bootstrap `docs/codebase/`.
## Tools / MCP
Claude supports rich tool use. The orchestrator MCP server provides tools for this (see mcp-server/README.md and docs/reference/tools/multi-platform-tool-use.md). Enable via client MCP config (Cursor/Claude Desktop examples available).
