# Pattern: Cache Freshness Watch (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekly synthesis of `docs/codebase/` cache staleness, branch drift vs TODO, and rebuild recommendations. Feeds `STATE.md` and `reports/loops/`.

## Cadence

- Cron: Mondays 09:30 UTC (`.github/workflows/loop-weekly-watch.yml` job `cache-freshness`)
- Manual: `/chain cache-freshness-watch` or maker `/cache-freshness-check` per this pattern

## Cache files (required)

1. `.github/project-manifest.yaml` — `token_policy.cache_stale_days`
2. `docs/codebase/.codebase-freshness.txt`
3. `docs/codebase/README.md` — `[UPDATED]` markers
4. Latest `TODO/*.md` — branch alignment
5. `STATE.md` — prior staleness flags

Max additional cache files: `loop_policy.max_cache_files_per_loop` (default 2).

## Maker / verifier

| Role | Skill |
|------|-------|
| Maker | `cache-freshness-check` |
| Verifier | `loop-verifier` |

## Host snapshot (optional)

`bash scripts/loop-cache-freshness-host.sh` writes `reports/loops/YYYY-MM-DD-cache-freshness-host.md` with JSON from `cache_freshness_check.py --json`.

## Outputs

- `reports/loops/YYYY-MM-DD-cache-freshness.md`
- Updated `STATE.md` (Stale flags, Last session), `loop-run-log.md`

## L1 rules

- `max_source_files: 0`
- No commits, PRs, or `/read-codebase` unless status is `stale` and user approves in Next section
- Executive summary ≤120 words
- Report must cite checker output and recommend `/chain cache-rebuild` when stale
- Report includes `## Lessons`; after verifier PASS run `loop-compound.sh`