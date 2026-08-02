# Cyber Essentials assessment — session + manifest install (code slice)

**Date:** 2026-07-20  
**Mode:** assess (code/CI)  
**Scope:** new session-start / eod resume-card / project-manifest bootstrap + deploy hard-block  
**Cyber Essentials:** mode=assess scope=session-manifest-install  

**Certification readiness (code slice only):** **partial** — engineering controls OK for this change set; org/perimeter items out of scope.

## Cache used

- `docs/codebase/CONCERNS.md`
- CSE scan + `scripts/session-security-sweep.sh` → overall=PASS  
- `reports/security/session-sweep-2026-07-20.md`

## Control summary

| # | Control | Status | Notes for this change set |
|---|---------|--------|---------------------------|
| 1 | Firewalls | n/a → pass (template) | No new network listeners, CORS, or public binds in changed code |
| 2 | Secure configuration | **pass** | `yaml.safe_load` only; no secrets written into manifests; no debug flags |
| 3 | User access control | **pass** | No auth surface; deploy preserves app identity; residue amend only on template names |
| 4 | Malware protection | **pass** | No executable payload paths; lockfiles/CI workflows unchanged; secrets sweep PASS |
| 5 | Security update management | **pass** (repo) | Dependabot + security-malware / mcp-security workflows present (repo-level) |

## Findings

### CE-001 — fixed — Manifest deploy bypass via path normalize (was BH-001)

**Control:** 2 / 3  
**Severity:** high (pre-fix)  
**Evidence:** `is_protected_manifest_rel` used `lstrip("./")` → `.github/...` unmatched.  
**Remediation:** fixed same session; hard never_deploy still lists manifests.

### CE-002 — pass — No secrets in resume cards / envelope

**Evidence:** resume card content is branch/TODO/HEAD; vault scrub still applies to vault emit.  
**Note:** resume cards may mention open TODO text — treat as untrusted data per AI content guardrails (existing).

### CE-003 — pass — Auto-switch does not discard WIP

**Evidence:** dirty tree → `blocked_dirty`; force-dirty does not override.  
**Control:** integrity / secure configuration of operator workflow.

### CE-004 — partial — EOD dirty after vault/resume write

**Control:** 2 (process)  
**Severity:** low  
**Evidence:** vault + resume write after clean gate. Mitigated with operator commit hint + chain args.  
**Org gap:** none; process fix still ideal.

### CE-005 — out-of-code

Perimeter firewall, board Cyber Essentials questionnaire, endpoint AV — **not** assessed here.

## Session security sweep

| Field | Value |
|-------|--------|
| overall | **PASS** |
| secrets | pass |
| cse_warns | 0 |
| report | `reports/security/session-sweep-2026-07-20.md` |

## Handoffs

- security-audit: not required for this slice (no auth/payment)
- bug-hunter: complete (see `reports/bugs/2026-07-20-bug-hunt-session-manifest.md`)
- drift-guardian: n/a for this assessment

## Sign-off

**Code slice CSE:** PASS with residual process note CE-004.  
**Not a full Cyber Essentials certificate.**
