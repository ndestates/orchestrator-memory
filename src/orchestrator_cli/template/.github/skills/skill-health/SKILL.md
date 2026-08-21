---
name: skill-health
description: "Read skill-health scores and verified_at/covers drift. Use after self-regulating skills, weekly, or when quality may have silently dropped."
argument-hint: "scan | summary | log --skill NAME --score 0.0-1.0"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
verified_at: "2026-08-16"
self_regulating: true
covers:
  - scripts/skill_health.py
  - .grok/references/self-regulating-loop.md
  - .github/skills/skill-health/SKILL.md
---
# Skill Health

Catalog observer for the self-regulating cohort. **Report-only.** Do not auto-edit skills.

## Commands

```bash
python3 scripts/skill_health.py scan
python3 scripts/skill_health.py summary
python3 scripts/skill_health.py log --skill <name> --score 0.0-1.0 --notes "<short>" [--corrected]
```

`--notes` must not contain secrets, tokens, or personal data. The script redacts common secret shapes.

## When

- After `/loop-compound` or weekly next to `/cache-freshness-check`
- When a self-regulating skill may have gone stale
- After a model or API change that could drop quality

## Output

```markdown
skill_health: stale=N score_flags=M missing_verified_at=K
recommend: bump verified_at | amend skill | no action
```

## Self-regulation (mandatory)

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**This skill's checks:**
- Ran `scan` and/or `summary` (did not invent scores)
- No secrets in any printed notes
- Did not auto-amend skills

Then: `python3 scripts/skill_health.py log --skill skill-health --score 0.0-1.0 --notes "scan|summary"`
