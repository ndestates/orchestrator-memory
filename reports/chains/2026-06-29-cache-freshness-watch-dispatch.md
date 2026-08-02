# Chain Dispatch — 2026-06-29

**Chain:** `cache-freshness-watch`
**Trigger:** workflow_dispatch (`run-chain.yml`)
**Host prep:** `scripts/loop-cache-freshness-host.sh`

## Registry

```
name: Cache Freshness Watch
tier: low
steps: cache-freshness-check (skill), loop-verifier (skill)
```

## Agent steps (cache-first)

1. Load manifest + chain cache from `chains/registry.yaml`
2. Run `/chain cache-freshness-watch scheduled` (skips confirm when in `chain_policy.scheduled_allowlist`)
3. On completion: `bash scripts/chain-completion-write.sh --chain-id cache-freshness-watch --outcome PASS --cache "<paths>" --artifact "<report>"`
4. For watch chains: run `/loop-verifier` on the final artifact

## Artifacts

- This dispatch note: `reports/chains/2026-06-29-cache-freshness-watch-dispatch.md`
- Loop host snapshots (if any): `reports/loops/*-host.md`
