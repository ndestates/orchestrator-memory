# Chain Dispatch — 2026-06-29

**Chain:** `session-start`
**Trigger:** workflow_dispatch (`run-chain.yml`)
**Host prep:** `(none)`

## Registry

```
name: Session Start
tier: low
steps: load-project-cache-first (prompt), changelog-specialist (skill), daily-standup-with-cache (skill), token-usage-meter (skill), cache-efficient (skill)
```

## Agent steps (cache-first)

1. Load manifest + chain cache from `chains/registry.yaml`
2. Run `/chain session-start scheduled` (skips confirm when in `chain_policy.scheduled_allowlist`)
3. On completion: `bash scripts/chain-completion-write.sh --chain-id session-start --outcome PASS --cache "<paths>" --artifact "<report>"`
4. For watch chains: run `/loop-verifier` on the final artifact

## Artifacts

- This dispatch note: `reports/chains/2026-06-29-session-start-dispatch.md`
- Loop host snapshots (if any): `reports/loops/*-host.md`
