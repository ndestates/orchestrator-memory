# Pattern: Repo Health Watch (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekly synthesis of branch hygiene, protected-branch alignment, open PRs, working-tree status, and drift flags. Lighter than on-demand `repo-health`; feeds `STATE.md` and `reports/loops/`.

## Cadence

- Cron: Mondays 09:30 UTC (`.github/workflows/loop-weekly-watch.yml` job `repo-health`)
- Manual: `/chain repo-health-watch`

## Cache files (required)

1. `docs/codebase/CONVENTIONS.md` — branch promotion model
2. `docs/codebase/INTEGRATIONS.md` — GitHub workflow summary
3. `docs/github/repo-health.md` — EOD checklist (if present)
4. `STATE.md` — prior repo-health flags
5. `LOOP.md` — confirm L1

Max additional cache files: `loop_policy.max_cache_files_per_loop`.

## Maker / verifier

| Role | Skill |
|------|-------|
| Maker | `github-expert` then `git-workflow-guardrails` (L1 report only) |
| Verifier | `loop-verifier` |

## Host snapshot (optional)

`bash scripts/loop-repo-health-host.sh` writes `reports/loops/YYYY-MM-DD-repo-health-host.md` with git branch status, divergence counts, and `gh pr list`.

## Optional host commands (≤3, after cache)

- `git fetch origin --prune` (read-only)
- `git rev-list --left-right --count origin/develop...develop` and same for `master`
- `gh pr list --limit 10`

## Outputs

- `reports/loops/YYYY-MM-DD-repo-health.md`
- Updated `STATE.md`, `loop-run-log.md` (via `scripts/chain-completion-write.sh` after chain)

## L1 rules

- `max_source_files: 0`
- No commits, pushes, branch deletes, or PR merges
- Executive summary ≤120 words
- `## Lessons` required; after verifier PASS run `loop-compound.sh`
- Stale local `feature/*` branches → recommend human cleanup; do not delete at L1
- Divergence or dirty tree → recommend `/chain repo-health` (full) or human action