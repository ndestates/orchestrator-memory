# Cache Freshness Host Snapshot — 2026-06-29

**Level:** L1 host-only (agent completes report via `/chain cache-freshness-watch`)

## Checker output (text)

```
Cache freshness: FRESH
Policy: cache_stale_days=14 (.github/project-manifest.yaml)
Last cache activity: 2026-06-29 (0 days ago)
Branch: feature/monday-loop-watches-2026-06-29
TODO branch: develop
Branch drift: YES — git=feature/monday-loop-watches-2026-06-29 vs TODO=develop
Recommend:
  - /chain cache-rebuild or targeted /read-codebase on current branch
  - /branch-context-agent
```

## Checker output (JSON)

```json
{
  "checked_at": "2026-06-29",
  "manifest": ".github/project-manifest.yaml",
  "cache_stale_days": 14,
  "last_scan_date": "2026-06-23",
  "last_readme_updated": "2026-06-29",
  "last_cache_activity": "2026-06-29",
  "age_days": 0,
  "status": "fresh",
  "branch_drift": true,
  "drift_reasons": [
    "git=feature/monday-loop-watches-2026-06-29 vs TODO=develop"
  ],
  "current_branch": "feature/monday-loop-watches-2026-06-29",
  "todo_branch": "develop",
  "scan_branch": null,
  "todo_file": "TODO/2026-06-29_TODO.md",
  "recommendations": [
    "/chain cache-rebuild or targeted /read-codebase on current branch",
    "/branch-context-agent"
  ],
  "files_checked": [
    "docs/codebase/.codebase-scan.txt",
    "docs/codebase/README.md"
  ]
}
```

## Next (human / agent)

1. Run `/cache-freshness-check` or `/chain cache-freshness-watch` per patterns/cache-freshness-watch.md
2. Write `2026-06-29-cache-freshness.md` and update STATE.md
3. Run `/loop-verifier` on final artifact
