# Pattern: Security Flywheel Watch (L1)

**Cache is king.** Report-only. No auto-fix.

## Purpose

Weekly **find-layer** snapshot of the Chrome-style security lifecycle:
doctrine files, session sweep, secrets/MCP signals, optional peer apps
across sibling apps. Feeds `reports/loops/`.

Canonical: [`SECURITY.md`](../SECURITY.md) · [`docs/guides/security-flywheel.md`](../docs/guides/security-flywheel.md)

## Cadence

- Manual / Monday-style: `bash scripts/loop-security-flywheel-host.sh`
- Agent depth: `/chain security-flywheel`
- Peers: `bash scripts/security-flywheel-status.sh --peers`

## Cache files (required)

1. `SECURITY.md`
2. `docs/guides/security-flywheel.md`
3. `docs/reference/stronger-with-every-update.md` (if present)
4. `LOOP.md` / `STATE.md` (flags only)

Max additional: `loop_policy.max_cache_files_per_loop`.

## Maker / verifier

| Role | Tool |
|------|------|
| Maker (host) | `scripts/loop-security-flywheel-host.sh` |
| Maker (agent) | `/chain security-flywheel` |
| Verifier | `loop-verifier` when agent writes a loop report |

## L1 rules

- Host job: prefer `--quick` (no long sweeps in CI)
- `max_source_files: 0` for host
- No auto-fix, no secret print
- FAIL → S0/S1 triage; WARN → S2 TODO

## Outputs

- Host: `reports/loops/YYYY-MM-DD-security-flywheel-host.md`
- Status: `reports/security/flywheel-status-YYYY-MM-DD.md`
