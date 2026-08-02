# Documentation refresh — 2026-06-29

**Chain:** documentation-refresh (scope: refresh)
**Repo class:** template

## Human site

- Hub: `docs/index.md`
- Refreshed: 11 pages across guides, reference, operations, getting-started, codebase cache
- Outline: `reports/docs/.doc-outline-2026-06-29.md`

## Cache updated

- `docs/codebase/README.md`
- `docs/codebase/ARCHITECTURE.md`
- `docs/codebase/STRUCTURE.md`
- `docs/codebase/INTEGRATIONS.md`
- `docs/codebase/TESTING.md`
- `docs/codebase/CONVENTIONS.md`

## Content policy

Pass — no secrets, trade secrets, or coding tips flagged.

## Gaps

1. No dedicated `docs/guides/loops.md` — weekly ritual lives in `daily-workflow.md` + `patterns/chain-health-watch.md` (acceptable for template).
2. `docs/reference/chains.md` table is curated subset; full list remains in `CHAIN.md` / registry.

## Next

1. Merge PR #74 (Phase A/B) then re-run refresh if registry changes land on develop.
2. Consider `docs/guides/loops.md` if loop surface grows further.
3. Run `/chain eod-shutdown` when session ends.