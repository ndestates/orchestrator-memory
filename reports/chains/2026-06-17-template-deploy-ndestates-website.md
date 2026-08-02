# Template deploy — ndestates-website

**Date:** 2026-06-17  
**Source:** ndestates/orchestrator @ `39dc6d6`  
**Target:** `/home/nickd/projects/ndestates-website`  
**Selections:** `grok,chains,loops,scripts`

## Result

- **99 new files** deployed (greenfield; 0 conflicts)
- Backup: `.grok/deploy-backups/2026-06-17T155049Z`
- Post-deploy: sync mirrors, name alignment PASS, chain-audit **100/100** (2 pre-existing prompt gaps)

## Project scaffold (manual, not in bundle)

- `.claude/project-manifest.yaml` + `.github/project-manifest.yaml` (Go, SQLite, Docker)
- `docs/codebase/README.md`, `ARCHITECTURE.md` (stub)
- `TODO/TODO-2026-06-17.md`

## Commit

- `ndestates-website`: initial orchestrator adoption commit on `master` (app source still untracked)

## Known gaps (template-level)

- `prompt/orchestrator-v2` — chain `complex-task`
- `prompt/beta-ready-checklist` — chain `beta-ready`

## Next

- Run `/read-codebase` on ndestates-website when ready
- Add git remote and push when GitHub repo exists
- Commit app source separately when operator is ready