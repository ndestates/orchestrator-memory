# Loop Vision (standing spec)

Read this file at the **start of every loop run** before maker work. State tells the agent where it is; this file tells it where to go.

## North star

Design systems that prompt agents — not hand prompts. **Cache is king:** manifest → lean cache → minimal host snapshot → report. Compound learning + secure vault graph: each iteration captures lessons into a hash-chained, provenance-rich, scrubbed ledger (`reports/vault/events.jsonl`) that enables self-building synthesis, tamper detection, and lean verified context across sessions/devices.

## Non-negotiables

| Rule | Enforcement |
|------|-------------|
| Cache-first | `loop_policy.cache_first_mandatory` |
| L1 default | Report-only; no auto-fix without approval |
| Objective gates | `loop-audit.sh`, `chain-audit.sh`, `git-push-secrets-guard.py` |
| Maker/checker split | `loop-verifier` on every loop artifact |
| Lessons every run | `## Lessons` in report → `scripts/loop-compound.sh` |
| Branch promotion | `feature/*` → `develop` → `master` |

## Cost discipline

Optimize **cost per accepted change**, not tokens spent. If human acceptance of loop output falls below 50%, pause scheduling and fix the gate.

## Comprehension debt (step 13)

- Read diffs on any loop-opened PR; spot-check gates quarterly.
- Keep loops on machine-checkable work (lint, audit, cache, CI triage) — not architecture or auth redesign at L1.

## Security tax (step 14)

- Re-audit loop permissions and skill sources every 30 days.
- Never auto-install unaudited community skills.
- Secrets guard on every wave deploy commit-push.

## Related

- Spine: `STATE.md`, `loop-run-log.md`, `reports/loops/lessons-state.json`
- Compound: `patterns/compound-learning.md`, `/loop-compound`
- Registry: `LOOP.md`, `patterns/registry.yaml`