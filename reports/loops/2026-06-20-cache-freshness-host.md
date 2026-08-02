# Cache Freshness Host Snapshot — 2026-06-20

**Level:** L1 host-only (agent completes report via `/chain cache-freshness-watch`)

## Checker output (text)

```
Cache freshness: FRESH
Policy: cache_stale_days=14 (.github/project-manifest.yaml)
Last cache activity: 2026-06-17 (3 days ago)
Branch: feature/work-2026-06-21
TODO branch: feature/eod-orchestrator-2026-06-21
Branch drift: YES — git=feature/work-2026-06-21 vs TODO=feature/eod-orchestrator-2026-06-21
Recommend:
  - /chain cache-rebuild or targeted /read-codebase on current branch
  - /branch-context-agent
```

## Checker output (JSON)

```json
{
  "checked_at": "2026-06-20",
  "manifest": ".github/project-manifest.yaml",
  "cache_stale_days": 14,
  "last_scan_date": null,
  "last_readme_updated": "2026-06-17",
  "last_cache_activity": "2026-06-17",
  "age_days": 3,
  "status": "fresh",
  "branch_drift": true,
  "drift_reasons": [
    "git=feature/work-2026-06-21 vs TODO=feature/eod-orchestrator-2026-06-21"
  ],
  "current_branch": "feature/work-2026-06-21",
  "todo_branch": "feature/eod-orchestrator-2026-06-21",
  "scan_branch": null,
  "todo_file": "TODO/2026-06-21_TODO.md",
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
2. Write `2026-06-20-cache-freshness.md` and update STATE.md
3. Run `/loop-verifier` on final artifact
