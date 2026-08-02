# Chain report: template-deploy (branch resume)

**Date:** 2026-06-17  
**Chain:** `template-deploy`  
**Source:** `7a75074`  
**Selections:** `grok,chains,loops,scripts` (skip customized) + targeted standup file push

## Targets

| App | Bundle deploy | Standup rule | Alignment | chain-audit |
|-----|---------------|--------------|-----------|-------------|
| project | +41 new, 5 skipped | OK | PASS | 100/100 (2 prompt gaps) |
| e-ndsign | +41 new, 51 skipped | OK | PASS | 100/100 (2 prompt gaps) |
| lightstone | +59 new, 33 skipped | OK | 2 proj-only issues | 100/100 |
| jerseyhouseprices | +48 new, 47 skipped | OK | PASS (after registry fix) | 100/100 (2 prompt gaps) |

**Backup id (all):** `2026-06-17T142048Z`

## Notes

- `daily-standup-with-cache` was skipped on conflict during bundle deploy; pushed via targeted copy + `sync_grok_to_github_claude.py`.
- jerseyhouseprices `chains/registry.yaml` redeploy dropped project skills — re-registered `daily-standup` and `security-checklist`.

## Next

- Commit app-repo changes per project workflow.
- Optional: `github,claude,copilot` selection deploy where mirrors still stale.