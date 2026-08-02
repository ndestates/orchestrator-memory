# Orchestrator Template — Repo Cache

[UPDATED 2026-06-23]

## What this repo is

`ndestates/orchestrator` — **project-agnostic AI orchestration template**. Ships `.grok/` skills, synced `.github/` + `.claude/` targets, loop engineering (L1 triage), and `/chain` skill composition. Not an application codebase.

## Quick commands

```bash
python3 scripts/sync_grok_to_github_claude.py   # after .grok/ edits
bash scripts/chain-audit.sh                       # validate chains
bash scripts/loop-audit.sh                        # validate loops
```

## Session defaults

- `/chain session-start` or `/load-project-cache-first`
- `/chain loop-daily` for triage
- `no chain` to opt out of multi-step runs
- `/script-not-shell` when multi-line shell would fail (CONCERNS §6) — write `scripts/` or `/tmp/agent-*`

## Branch flow

`feature/*` → `develop` → `master` via `branch-promotion-prs.yml`

## Key paths

- Manifest: `.github/project-manifest.yaml`
- Chain registry: `CHAIN.md`, `chains/registry.yaml`
- Loop state: `STATE.md`, `reports/loops/`
- Latest TODO: `TODO/2026-06-21_TODO.md`
- Cache index: `docs/codebase/README.md` (refreshed 2026-06-23)

## Workflows

`release.yml`, `repository-sync.yml`, `loop-daily-triage.yml`, `loop-weekly-watch.yml`, `chain-audit.yml`, `branch-promotion-prs.yml`

## MCP server (dev-only)

`mcp-server/` — read-only cache tools; path sandbox (`PROJECT_ROOT` + prefix allowlist), bearer auth on HTTP, JSONL audit → `reports/mcp/`. Threat scan: `bash scripts/mcp-threat-scan.sh`.