# Pattern: Version Drift Watch (L1)

**Cache is king.** Report-only. No auto-fix / no fleet wave. **Scaffold — manual until scheduled.**

## Purpose

Compare **template** version (`VERSION` / `scripts/orchestrator-template-version`) with **per-app** `.orchestrator-version` locks (and optional `orchestrator status`). Surfaces apps still on older template after a release so humans can run [per-app upgrade](../docs/guides/per-app-upgrade.md).

## Cadence

- **Manual (default):** `/chain version-drift-watch` (e.g. after tagging a release)
- **Optional later:** Monday weekly or post-release workflow_dispatch
- Host snapshot: `bash scripts/loop-version-drift-host.sh`

## Cache files (required)

1. `VERSION` or `scripts/orchestrator-template-version`
2. `STATE.md`
3. `docs/guides/per-app-upgrade.md` (or `docs/codebase/INTEGRATIONS.md` if guide not in cache cap)
4. `LOOP.md`
5. Latest `TODO/*.md` — open upgrade items

Max additional cache files: `loop_policy.max_cache_files_per_loop`.

## Maker / verifier

| Role | Skill / command |
|------|-----------------|
| Maker | `loop-engineering` + host script; optional `github-expert` for open upgrade PRs |
| Verifier | `loop-verifier` |

## Host snapshot

```bash
bash scripts/loop-version-drift-host.sh
# Default: **active project only** (this repo). Never walks ~/projects.
# Optional multi-app (explicit): ORCHESTRATOR_APPS="app1 app2" PROJECTS_ROOT=~/projects
```

For the active project (or each **explicit** ORCHESTRATOR_APPS slug):

- Read `.orchestrator-version` / `VERSION` → lock or `none`
- Compare to template VERSION
- Note dirty tree / branch (informational)

**Do not** run `orchestrator upgrade` at L1. **Do not** default to a fleet sibling list.

## Outputs

- `reports/loops/YYYY-MM-DD-version-drift.md`
- Host: `reports/loops/YYYY-MM-DD-version-drift-host.md`
- `STATE.md` / `loop-run-log.md` via chain completion

## Report must include

1. Template version  
2. Table: app | lock | status (`current` / `behind` / `no_lock` / `missing`)  
3. Suggested human actions: `orchestrator upgrade /path --no-pr` per app  
4. **## Lessons**  
5. Explicit: **no fleet wave**

## L1 rules

- `max_source_files: 0`
- No fleet wave (tooling deleted)  
- No commits/pushes to app repos  
- Dirty apps → recommend stash/commit; do not force upgrade  
- After verifier PASS → `loop-compound.sh`

## Related

- [When to use loops](../docs/guides/when-to-use-loops.md)  
- [Per-app upgrade](../docs/guides/per-app-upgrade.md)  
