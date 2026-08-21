# Loop Token Budget

Aligns with `.github/project-manifest.yaml` → `token_policy` and `loop_policy`.

## Global rules

- **Cache is king:** manifest → cache index → ≤3 targeted cache files → memories INDEX (≤3) → then optional host snapshot.
- Default response cap for L1 loops: **≤120 words** (same as `/cache-efficient`).
- No full `read-codebase` on scheduled runs unless `.codebase-scan.txt` is stale.

## Per-loop budgets

| Loop | Cadence | Max cache files | Max source files | Sub-agents | Token tier |
|------|---------|-----------------|------------------|------------|------------|
| daily-triage | 1d | 2 + TODO + STATE | **0** at L1 | verifier only | low |
| cache-freshness-watch | 1w (Mon) | 2 + freshness + TODO | **0** | verifier only | low |
| chain-health-watch | 1w (Mon) | 2 + registry grep | **0** | verifier only | low |
| github-ci-watch | 1w (Mon) | 2 + INTEGRATIONS | **0** | verifier only | low |
| repo-health-watch | 1w (Mon) | 2 + CONVENTIONS | **0** | verifier only | low |
| branch-promotion-watch | event | 2 | 0 | 0 | low |
| compound-learning | on_demand | 3 + VISION + STATE | **0** | 0 | low |

## Escalation

- Exceeding budget → downgrade to L1 report-only for that run.
- L2+ requires explicit `loop_policy.allow_l2` and human approval in STATE Open queue.

## Cost control

- Triage uses fast/lean model tier; implementer sub-agents spawn only when STATE marks item actionable.
- Verifier reads **artifacts only** (`reports/loops/*.md`, `git diff` summary) — not full codebase.