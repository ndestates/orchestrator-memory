# Chain report: template-deploy → apps

**Date:** 2026-06-18  
**Chain:** `template-deploy`  
**Source:** orchestrator `37e2643` → `c99f204` (wave scripts)  
**Method:** `scripts/deploy-template-wave.sh` (grok + chains + loops + scripts; preserve project skills)

## Targets

| App | Branch | Commit | Pushed | chain-audit |
|-----|--------|--------|--------|-------------|
| project | `feature/admin-auth-pest-tests` | `9a4b0e5` | Yes | 100/100 (2 prompt gaps) |
| e-ndsign | `feature/laravel-e-ndsign-scaffold` | `767c20c` | Yes | 100/100 (2 prompt gaps) |
| jerseyhouseprices | `feature/ddev-eod` | `2d52399` | Yes | 100/100 (2 prompt gaps) |
| lightstone | `feature/orchestrator-standup-resume-2026-06-17` | `f06d1e36` | Yes | 100/100 (1 prompt gap) |

## Notes

- Removed orchestrator `__pycache__` before deploy (was breaking `deploy_grok_to_project.py` UTF-8 read).
- **jerseyhouseprices:** registry restored (`daily-standup`, `security-checklist`) after bundle copy.
- **lightstone:** preserved project skills (`orchestrator`, `scope-creep-detector`, `token-meter-usage`, etc.).
- Pre-existing alignment noise on lightstone (proj-only skills) — non-blocking; audit score 100.

## Next

- Optional: copy `scripts/deploy-template-wave.sh` to app repos on next wave.
- Merge app feature branches via normal PR workflow.