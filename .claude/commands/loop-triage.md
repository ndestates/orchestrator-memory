---
description: L1 daily loop triage for the orchestrator template.
argument-hint: Optional focus, e.g. 'PRs', 'workflows', 'TODO carry'
allowed-tools: Read, Grep, Glob, Bash
---

# Loop Triage (L1, cache-first)

**Cache is king.** This loop does not explore the codebase. It reads cached knowledge and minimal host snapshots.

## Mandatory load order (do not skip)

1. `VISION.md` — standing spec (where to go; read before maker work)
2. Your platform manifest (`.grok/project-manifest.yaml` for Grok; full table + paths in `docs/reference/manifest.md`) — `paths`, `token_policy`, `loop_policy`
3. `LOOP.md` — confirm level **L1** for this run
4. `loop-budget.md` — respect max cache files and zero source files at L1
5. `STATE.md` — resume open queue + `Lessons → skills`; do not duplicate done items
6. `reports/loops/lessons-state.json` — prior lessons (sections only if large)
7. `docs/codebase/README.md` + `docs/codebase/.codebase-scan.txt` — staleness only (or `/cache-freshness-check`)
8. **≤3 targeted sections** from `docs/codebase/CONCERNS.md`, `ARCHITECTURE.md`, or `CONVENTIONS.md` (grep headings; no full-file read unless small)
9. Latest `TODO/*.md` — open items in ≤5 bullets
10. `.copilot/memories/INDEX.md` — ≤2 memories if relevant

## Optional host snapshot (after cache only)

Only if needed for the report; cap at 3 commands:

- `git branch --show-current` + `git status --short`
- `gh pr list --limit 5` (if `gh` available)
- `gh run list --limit 3` (if `gh` available)

Do **not** run grep/find across source trees at L1.

## Produce (L1)

1. Write `reports/loops/YYYY-MM-DD-triage.md` with:
   - **Cache cited:** list every file/section used
   - **Priorities:** ≤5 bullets from cache + TODO
   - **Risks:** numbered CONCERNS items touched
   - **Host snapshot:** branch, open PRs (if fetched)
   - **Lessons:** ≥1 bullet (concrete learning) or `- none new`
   - **Next:** 1–3 human actions (no auto-fix)
2. Update `STATE.md` — Cache used, Open/Done, Last session
3. Append one row to `loop-run-log.md`
4. Stay ≤120 words in the executive summary at top of report

## Chain verifier + compound

1. Invoke `/loop-verifier` on the report artifact before marking run complete.
2. On verifier **PASS**, run `bash scripts/loop-compound.sh --report <artifact>` (`/loop-compound`).

## Anti-patterns

- Reading `app/`, `src/`, or large trees before cache load
- Auto-commits, auto-PRs, or fixes at L1
- Pasting large cache paragraphs into the report (cite by section only)

User focus (optional): $ARGUMENTS
