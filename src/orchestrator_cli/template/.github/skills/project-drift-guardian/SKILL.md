---
name: project-drift-guardian
description: "Guard against project and skill-contract drift: cache vs source, TODO vs branch, verified_at/covers. Use before deploy, upgrade, or when scope may have crept."
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
verified_at: "2026-08-16"
self_regulating: true
covers:
  - .github/skills.github/skills/project-drift-guardian/SKILL.md
  - scripts/skill_health.py
  - docs/codebase/CONCERNS.md
  - STATE.md
---
# Project Drift Guardian

Prevents **silent drift** of this repo (orchestrator template or a forked app): scope vs TODO, cache vs tree, skill contracts (`verified_at`/`covers`), and — only when the manifest says so — schema/deploy assumptions.

This is **not** an app-specific e-sign or hosting playbook. Read the **local** manifest + cache for product facts.

## Mandatory start

1. `.github/prompts/load-project-cache-first.prompt.md` — CONCERNS, TODO branch, freshness.
2. `python3 scripts/skill_health.py scan --json` — skill-contract drift.
3. `python3 .github/skills/cache-freshness-check/scripts/cache_freshness_check.py --json` — cache age.
4. Optional: `./.github/skills.github/skills/project-drift-guardian/SKILL.md/scripts/drift-check.sh`

Report-only at L1. Do not auto-fix, overwrite customized skills, or deploy.

## What to check

| Type | Signal | Next |
|------|--------|------|
| Skill contract | `skill_health.py scan` stale or missing `verified_at` | `/skill-health`; bump `verified_at` after review |
| Cache staleness | freshness `stale` / `branch_drift` | `/cache-freshness-check` |
| Scope | git diff vs TODO / branch purpose | `/branch-context-agent` |
| Identity | `check-project-manifest.py` `template_residue` | do not trust stack until customized |
| Schema / deploy | only if `uses_database` or a deploy skill is in scope | `.github/prompts/model-schema-check.prompt.md`, hosting skill |

## Scripts

- `scripts/drift-check.sh` — git vs `origin/develop` (fallback `origin/master`), then skill scan + cache freshness
- `scripts/db_ops.sh` + `scripts/init_db.sql` — optional local sqlite requirements log (generic; no product seeds)

## Report

Use [references/alignment-report-template.md](references/alignment-report-template.md). Handoff:

```text
DriftGuardian: project=<name> | Branch: <b> | skill_stale=N | cache=<status> | Gate: PASS|WARN|BLOCK
```

## Self-regulation (mandatory)

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**This skill's checks:**
- Used manifest/cache, not a baked-in product story
- Ran skill scan + cache check (or recorded why not)
- Did not treat app-specific residue as requirements

Then: `python3 scripts/skill_health.py log --skill project-drift-guardian --score 0.0-1.0 --notes "scan"`
