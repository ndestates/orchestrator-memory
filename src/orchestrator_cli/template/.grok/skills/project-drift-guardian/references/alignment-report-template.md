# Alignment / drift report

**Project:** (from manifest `project.name`)
**Date:** YYYY-MM-DD
**Branch:**
**Cache loaded:** (yes + which)

## Executive summary

- Overall alignment: Strong / Minor drift / Significant drift
- Skill-contract stale: N
- Cache status:
- Recommendation: PROCEED / BLOCK / PROCEED with conditions

## Checks

- [ ] Manifest identity (`check-project-manifest.py`) is not unexpected residue
- [ ] `skill_health.py scan` — stale / missing `verified_at`
- [ ] Cache freshness vs `cache_stale_days`
- [ ] Branch vs latest TODO / branch purpose
- [ ] Schema/deploy (only if manifest/stack requires)

## Drifts

For each: type (skill | cache | scope | schema | deploy), evidence, severity, remediation.

## Next

1. …
