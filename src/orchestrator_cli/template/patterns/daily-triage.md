# Pattern: Daily Triage (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekday synthesis of priorities from cache + TODO + minimal host snapshot. Feeds `STATE.md` and `reports/loops/`.

## Cadence

- Cron: weekdays 09:00 UTC (`.github/workflows/loop-daily-triage.yml`)
- Grok: `/loop 1d Run loop-triage per patterns/daily-triage.md`
- Manual: `/loop-triage`

## Cache files (required)

1. `paths.loop_registry` → `LOOP.md`
2. `paths.loop_state` → `STATE.md`
3. `paths.docs_index` → `docs/codebase/README.md`
4. `docs/codebase/CONCERNS.md` (sections only)
5. Latest `TODO/*.md`

Max additional cache files: `loop_policy.max_cache_files_per_loop` (default 2).

## Maker / verifier

| Role | Skill / agent |
|------|----------------|
| Maker | `loop-triage` |
| Verifier | `loop-verifier` |

## Outputs

- `reports/loops/YYYY-MM-DD-triage.md`
- Updated `STATE.md`, `loop-run-log.md`

## L1 rules

- `max_source_files: 0`
- No commits, PRs, or code edits
- Executive summary ≤120 words
- Report includes `## Lessons` (≥1 bullet or `none new`)
- After verifier PASS: `bash scripts/loop-compound.sh --report <artifact>`