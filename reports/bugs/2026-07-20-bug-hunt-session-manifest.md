# Bug hunt — session auto-switch + project-manifest install

**Date:** 2026-07-20  
**Mode:** full (deep) + fix  
**Scope:** session-start auto-switch (`resume-branch`, envelope, resume cards); install manifest policy (`manifest_bootstrap`, deploy never_deploy, flow)  
**Branch:** `feature/context-window-literacy-2026-07-18`  
**Bug hunter:** mode=deep-fix scope=session+manifest-install  

## Cache used

- `VERSION` (1.8.6)
- `docs/codebase/CONCERNS.md`
- `scripts/_engine/manifest_bootstrap.py`, `deploy.py`, `session_envelope.py`
- `scripts/resume-branch.sh`, `session-resume-brief.py`, `eod-vault-emit.py`
- `src/orchestrator_cli/flow.py`
- Static: `bug-hunter-scan.sh` → `reports/bugs/scan-20260720-session-manifest.txt`

## Summary

| Severity | Open | Fixed | Suggested |
|----------|------|-------|-----------|
| critical | 0 | 0 | 0 |
| high | 0 | 2 | 0 |
| medium | 1 | 3 | 1 |
| low | 0 | 1 | 1 |
| info | 2 | 0 | 0 |

**Tests:** `test_manifest_bootstrap`, `test_resume_branch`, `test_session_resume_brief` — PASS after fixes.

---

## Findings

### BH-001 — HIGH — `is_protected_manifest_rel` broke via `str.lstrip("./")`

**Status:** fixed  
**Category:** logic / security-adjacent  

`lstrip("./")` strips **any** of the characters `.` and `/` from the left, so  
`.github/project-manifest.yaml` became `github/project-manifest.yaml` and **failed** the allowlist match. Manifest protection was effectively off for all `.github`/`.claude`/… paths until fixed.

**Fix:** normalize with `while startswith("./")` only; re-tested.

### BH-002 — HIGH — `git checkout -B` risk on new branch create

**Status:** fixed  
**Category:** data integrity  

New-branch path used `checkout -B`, which can reset an existing local ref if present. Replaced with create/`-b`/`--track` only (never reset).

### BH-003 — MEDIUM — post-switch `git pull` always run

**Status:** fixed  
**Category:** error handling  

Pull ran even when already at tip; fake/offline remotes reported `switched_pull_failed` falsely. Now pulls only when `current_behind > 0`; failures set `switched_pull_failed` only then.

### BH-004 — MEDIUM — `--force-dirty` claimed to override dirty block

**Status:** fixed  
**Category:** config / safety  

Comment suggested force could switch dirty trees; implementation was inconsistent. Dirty always blocks; flag accepted but ignored (documented).

### BH-005 — MEDIUM — EOD vault + resume card dirty clean-git gate

**Status:** fixed (partial — process)  
**Category:** process / eod  

`eod-vault-emit.py` writes vault events + rich resume card **after** the clean-git step, leaving porcelain dirty (pre-existing for vault; worsened by resume card).  

**Fix:** emit prints dirty-path count + commit hint; eod-shutdown chain skill_args require post-emit commit for clean EOD.

**Suggested (not auto-fixed):** reorder cleanup to commit vault/resume inside final gate (larger process change).

### BH-006 — LOW — dead / confusing stack amend branches

**Status:** fixed  
**Category:** maintainability  

`elif force_identity` was unreachable; runtime overwrite could clobber ddev with local. Restructured force vs soft amend.

### BH-007 — LOW — broad protection of any `project-manifest.yaml`

**Status:** fixed (scoped)  
**Category:** logic  

Protection limited to known platform roots (`.github`, `.grok`, …), not `docs/**/project-manifest.yaml`.

### BH-008 — INFO — YAML dump loses comments on seed/amend

**Status:** open (info)  
**Category:** UX  

`yaml.safe_dump` for seed/amend drops comment headers except the written header block. Acceptable for install.

### BH-009 — INFO — static scan clean

**Status:** open (info)  
Markers / raw SQL / eval / secrets: 0 on full-repo scan script.

---

## Fix log

| ID | File(s) | Change |
|----|---------|--------|
| BH-001 | `manifest_bootstrap.py` | Fix path normalize (no `lstrip("./")`) |
| BH-002 | `resume-branch.sh` | No `-B`; create-only checkout |
| BH-003 | `resume-branch.sh` | Pull only when behind |
| BH-004 | `resume-branch.sh` | Dirty always blocks |
| BH-005 | `eod-vault-emit.py`, `chains/registry.template.yaml` | Dirty warning + chain instruction |
| BH-006 | `manifest_bootstrap.py` | Amend logic cleanup |
| BH-007 | `manifest_bootstrap.py` + tests | Platform-root scoped protection |

**Rollback:** git checkout of listed files; no backup session (local uncommitted feature work).

---

## Handoff

```text
bug_hunt: 9 findings (0C/2H/3M/2L/2I); fixed=7; tests=pass
security_pending: none critical (see CSE report)
test_gaps: none for changed modules (smoke harness)
drift_flags: no
```
