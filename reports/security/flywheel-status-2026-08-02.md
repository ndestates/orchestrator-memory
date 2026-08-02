# Security flywheel status

- Generated: `2026-08-02T08:14Z`
- Branch: `feature/work-2026-08-02`
- HEAD: `70d86d2`
- Mode: quick
- Lifecycle: find → triage → fix → ship → prevent

| Stage key | Status | Detail |
|-----------|--------|--------|
| `find.security_md` | **PASS** | SECURITY.md present (trust boundaries) |
| `find.flywheel_guide` | **PASS** | docs/guides/security-flywheel.md present |
| `find.stronger_standard` | **PASS** | stronger-with-every-update standard present |
| `find.manifest_flag` | **PASS** | security_policy.stronger_with_every_update true |
| `find.dependabot` | **PASS** | Dependabot config present |
| `ship.secrets_guard` | **PASS** | git-push-secrets-guard.py present |
| `find.mcp_threat_scan` | **PASS** | mcp-threat-scan present |
| `find.session_sweep` | **PASS** | skipped (--quick) |
| `ship.bundle_hash` | **PASS** | bundle-hashes.json present |
| `prevent.always_on_memory` | **PASS** | always-on memory CLI present |
| `prevent.vault` | **PASS** | vault engine/ledger available |
| `prevent.flywheel_chain` | **PASS** | chain security-flywheel registered |
| `prevent.security_md_critic` | **PASS** | chains reference security flywheel / SECURITY.md |
| `prevent.mcp_off_default` | **PASS** | runtime.mcp defaults off |
| `find.laravel_app` | **PASS** | not a Laravel app tip (template/generic OK) |
| `peer.ndestates.security_md` | **PASS** | ndestates SECURITY.md present |
| `peer.ndestates.flywheel` | **PASS** | ndestates flywheel surface present |
| `peer.lightstone.security_md` | **WARN** | lightstone SECURITY.md missing |
| `peer.lightstone.flywheel` | **WARN** | lightstone flywheel not detected |

**PASS=17 WARN=2 FAIL=0**

Next: triage FAIL as S0/S1 per SECURITY.md; run `/chain security-flywheel` for CE + audit depth.
Peers: `bash scripts/security-flywheel-status.sh --peers` · Guide: docs/guides/security-flywheel.md
Memory: optional `orchestrator memory ingest --text "flywheel status PASS/WARN/FAIL" --source flywheel`
