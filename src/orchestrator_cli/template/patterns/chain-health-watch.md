# Pattern: Chain Health Watch (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekly validation of `chains/registry.yaml`, invoke targets, cache paths, and `scripts/chain-audit.sh` score. Surfaces broken chains, missing skills, and registry gaps before they break CI or delivery flows.

## Cadence

- Cron: Mondays 09:30 UTC (`.github/workflows/loop-weekly-watch.yml` job `chain-health`)
- Manual: `/chain chain-health-watch`

## Cache files (required)

1. `chains/registry.yaml`
2. `CHAIN.md` — active chains table vs registry
3. `LOOP.md` — loop/chains cross-reference
4. `docs/codebase/INTEGRATIONS.md` — sync targets section
5. `STATE.md` — open queue items touching chains

Max additional cache files: `loop_policy.max_cache_files_per_loop`.

## Maker / verifier

| Role | Skill |
|------|-------|
| Maker | `loop-engineering` (chain/registry scope only — run `chain-audit.sh`, grep registry) |
| Verifier | `loop-verifier` |

## Host snapshot (optional)

`bash scripts/loop-chain-health-host.sh` runs `chain-audit.sh` and writes `reports/loops/YYYY-MM-DD-chain-health-host.md`.

## Monday ritual (close the half-loop)

GitHub Actions writes **host snapshots only**; the agent completes the L1 chain. Run in order after the Monday `loop-weekly-watch` job (or download its artifact):

1. **Host artifact** — confirm `reports/loops/YYYY-MM-DD-chain-health-host.md` exists (from CI or `bash scripts/loop-chain-health-host.sh`).
2. **Maker chain** — `/chain chain-health-watch scheduled` (explicit id + `scheduled` skips confirm when allowlisted).
3. **Verifier** — `/loop-verifier` on `reports/loops/YYYY-MM-DD-chain-health.md`.
4. **Close the loop** — `bash scripts/chain-completion-write.sh --chain-id chain-health-watch --outcome PASS --cache "<paths>" --artifact reports/loops/YYYY-MM-DD-chain-health.md --steps "audit,verify"`.

Repeat the same shape for sibling watches: `cache-freshness-watch`, `github-ci-watch`, `repo-health-watch` (each has its own host script and pattern).

**One-click dispatch:** `.github/workflows/run-chain.yml` with `chain_id: chain-health-watch` runs host prep and writes `reports/chains/YYYY-MM-DD-chain-health-watch-dispatch.md`.

## Outputs

- `reports/loops/YYYY-MM-DD-chain-health.md`
- Updated `STATE.md`, `loop-run-log.md`

## L1 rules

- `max_source_files: 0`
- No edits to `chains/registry.yaml` or workflows at L1
- Executive summary ≤120 words
- `## Lessons` required; after verifier PASS run `loop-compound.sh`
- Report must include chain-audit score and list any FAIL/WARN invoke lines
- Next actions may suggest `/chain` registration or `python3 scripts/sync_grok_to_github_claude.py` — human executes