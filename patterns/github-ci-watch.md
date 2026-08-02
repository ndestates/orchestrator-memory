# Pattern: GitHub CI Watch (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekly synthesis of GitHub Actions workflow health: workflow inventory, recent failed runs, environment protection gaps, and secret *names* inventory (never values). Supports deploy readiness and `github-workflow-expert` follow-up.

## Cadence

- Cron: Mondays 09:30 UTC (`.github/workflows/loop-weekly-watch.yml` job `github-ci`)
- Manual: `/chain github-ci-watch`

## Cache files (required)

1. `docs/codebase/INTEGRATIONS.md` — workflow summary table
2. `.github/workflows/` — file list only (names, not full YAML bodies at L1)
3. `chains/registry.yaml` — deploy-check, github-workflow-setup entries
4. `STATE.md` — CI-related open items
5. `LOOP.md` — confirm L1

Max additional cache files: `loop_policy.max_cache_files_per_loop`.

## Maker / verifier

| Role | Skill |
|------|-------|
| Maker | `github-workflow-expert` |
| Verifier | `loop-verifier` |

## Host snapshot (optional)

`bash scripts/loop-github-ci-host.sh` writes `reports/loops/YYYY-MM-DD-github-ci-host.md` with `gh workflow list`, `gh run list --limit 10`, and workflow file listing.

## Optional host commands (≤3, after cache)

- `gh workflow list`
- `gh run list --limit 10 --json conclusion,name,displayTitle,updatedAt`
- `gh secret list` and `gh secret list --env production` (names only)

## Outputs

- `reports/loops/YYYY-MM-DD-github-ci.md`
- Updated `STATE.md`, `loop-run-log.md`

## L1 rules

- `max_source_files: 0` — list workflow files; do not read full job logic unless ≤40 lines for one file
- No `gh secret set`, no workflow edits, no commits
- Never print secret values
- Executive summary ≤120 words
- `## Lessons` required; after verifier PASS run `loop-compound.sh`
- Failed runs → recommend `/chain github-workflow-setup` or human fix; do not auto-dispatch fixes