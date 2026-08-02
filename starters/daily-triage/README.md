# Starter: Daily Triage L1

Copy into a downstream project (with orchestrator `.grok/` tree):

1. `LOOP.md`, `STATE.md`, `loop-budget.md`, `loop-run-log.md`
2. `patterns/daily-triage.md` + `patterns/registry.yaml`
3. `.grok/skills/loop-triage/` + `.grok/skills/loop-verifier/`
4. `scripts/loop-audit.sh`
5. `.github/workflows/loop-daily-triage.yml`
6. Add `loop_policy` + loop paths to `project-manifest.yaml`

Run `bash scripts/loop-audit.sh` then `/loop-triage` → `/loop-verifier`.

**Cache is king:** set `cache_files_required` in registry before enabling cron.