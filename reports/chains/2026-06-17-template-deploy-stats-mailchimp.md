# Template deploy — google-stats, facebook-stats, mailchimp

**Date:** 2026-06-17  
**Source:** ndestates/orchestrator @ `39dc6d6`  
**Policy:** `--non-interactive --default-action skip` (preserve differing files)

## Results

| Project | New | Skipped (conflicts) | Branch |
|---------|-----|---------------------|--------|
| google-stats | 92 | 7 | `feature/docker-hardened-images` |
| facebook-stats | 92 | 7 | `feature/codebase-knowledge-customizations` |
| mailchimp | 80 | 19 | `feature/audience-reporting` |

## Preserved (skipped) — google-stats & facebook-stats

- `.grok/prompts/read-codebase.md`
- `.grok/skills/daily-standup-with-cache/SKILL.md`
- `.grok/skills/ddev-local-runtime/SKILL.md`
- `.grok/skills/git-workflow-guardrails/SKILL.md`
- `.grok/skills/load-project-cache-first/SKILL.md`
- `.grok/skills/security-audit-agent/SKILL.md`
- `.grok/skills/todo-specialist-agent/SKILL.md`

## Preserved (skipped) — mailchimp

All 19 overlapping template skills/memories where local copies differed (e.g. `branch-context-agent`, `cache-efficient`, `laravel-expert-agent`, `read-codebase`, etc.). Project-only skills untouched: `orchestrator`, `production-push-db-guardrails`, `multi-faceted-instruction`, etc.

## Added (all projects)

- New template skills: `token-usage-meter`, `cache-efficient`, `chain`, `loop-*`, `bug-hunter-agent`, `cyber-security-essentials`, etc.
- `CHAIN.md`, `chains/registry.yaml`, `LOOP.md`, `loop-budget.md`, `patterns/`
- Deploy/audit scripts + report scaffolds

## Post-deploy

- Sync mirrors: OK
- Name alignment: WARN — project-only skills not in registry (expected)
- Chain-audit: **100/100** on all three (2 template prompt gaps each)

## Rollback

```bash
python3 scripts/deploy_grok_to_project.py /home/nickd/projects/<app> --rollback --backup-id <timestamp>
```

Backup IDs: google-stats `2026-06-17T162016Z`, facebook-stats/mailchimp `2026-06-17T162017Z`