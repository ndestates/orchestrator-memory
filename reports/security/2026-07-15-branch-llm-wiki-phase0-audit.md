# Security audit — `feature/llm-wiki-phase0-2026-07-15` (pre-push)

**Date:** 2026-07-15  
**Auditor:** security-audit-agent (read-only)  
**Scope:** Branch tip `ebfdf61` vs `origin/develop` (what a push + PR would expose)  
**Focus:** Phase 0 LLM Wiki policy commit + residual branch delta from base work branch  

---

## Sign-off

| Result | Detail |
|--------|--------|
| **Verdict** | **READY** to push |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low / informational | 2 (see Residual) |

No secrets, no executable payload in the Phase 0 tip commit, no malware-lint findings, session sweep **PASS**, secrets-guard **PASS** on full `origin/develop...HEAD` range.

---

## Cache cited

- `docs/codebase/CONCERNS.md` (§7 MCP, §9 wave, §10 vault, §12 supply chain, §13 LLM Wiki)
- `docs/codebase/README.md` (template surface map)
- `.github/project-manifest.yaml` (`wiki_policy`, `agent_policy`, vault paths)
- `reports/research/llm-wiki-karpathy-plan.md` (policy under audit)
- Prior session sweep pattern: `reports/security/session-sweep-2026-07-15.md`

---

## Tooling results

| Check | Range / target | Result |
|-------|----------------|--------|
| `git-push-secrets-guard.py` | `HEAD~1..HEAD` (Phase 0 only) | **OK** — 11 files |
| `git-push-secrets-guard.py` | `origin/develop...HEAD` | **OK** — 26 files |
| `session-security-sweep.sh --active-only` | this repo | **overall=PASS** · CSE warns=0 · hooks present |
| `orchestrator-malware-lint.py` | repo default | **critical=0 high=0 clean** |
| `scripts/ci_security_checklist.sh` | — | **N/A** (not present; no dep/form changes) |
| Manual secret-pattern scan | 26 changed paths | **no matches** (excluding placeholders) |
| Prompt-injection markers in plan | research memo | **none** |

Session sweep report path: `reports/security/session-sweep-2026-07-15.md`

---

## Change surface

### A. Phase 0 tip commit (`ebfdf61`) — primary ask

| Area | Files | Risk |
|------|-------|------|
| Manifest policy | 6× `project-manifest.yaml` platforms | **Low** — config only |
| Docs / research | CONCERNS, README, guides index, manifest ref, research plan | **Low** — markdown |
| Code / shell / deps | **none** | — |
| Auth / forms / MCP server | **none** | — |
| `wiki/` or `raw/` trees | **not created** (correct for Phase 0) | — |

**Policy defaults verified (safe-by-default):**

| Key | Value | Security note |
|-----|-------|----------------|
| `wiki_policy.mode` | `off` | No wiki ops until Phase 1 |
| `auto_ingest` | `false` | No silent ingest of untrusted sources |
| `require_approval_for_writes` | `true` | Human gate for multi-file writes |
| `l1_report_only` | `true` | Aligns L1 no-auto-fix |
| `deploy_selection` | `wiki` (name only) | Selection not wired in Phase 0; fleet still blocked elsewhere |
| `dual_write_vault` | `true` | Future dual-write; vault scrub path remains required in Phase 1 |

Non-goals in plan explicitly forbid fleet wiki wave, auto-ingest of chats/PRs, replacing vault, and vector RAG as primary path — reduces future blast-radius ambiguity.

### B. Full branch vs `origin/develop` (push may include base commits)

Also on this branch (inherited from `feature/work-2026-07-15` ancestry):

| Change | Security assessment |
|--------|---------------------|
| `scripts/session-security-sweep.sh` default **active-only**; fleet via `--all-repos` | **Positive** — reduces multi-repo scan blast / hang; report-only unchanged |
| Dirty-path cap during collection | **Positive** — DoS/hang resistance on huge dirty trees |
| Vault EOD events + workspace pointers | **Info** — operator email `nick@ndestates.com` is operational identity, not a secret |
| TODO / changelog / STATE | Process docs — no secrets found |
| `.gitignore` adds `.local/`, `bin/bin/`, `bin/lib/` | **Positive** — keeps local tooling out of git |

No auth, 2FA, consent/CDD, or permission model changes on this branch.

---

## Findings

### Critical / High / Medium

**None.**

### Low / informational

1. **Working tree untracked:** `reports/security/session-sweep-2026-07-15.md` (and this audit once written). Safe content; optional to commit. Do not force-add unrelated local dumps.  
2. **Future Phase 1 risk (tracked in CONCERNS §13):** When `mode` leaves `off`, `raw/` and `wiki/` become secret/PI surfaces. Phase 1 must wire secrets-guard paths + vault scrub + no auto-commit. **Not a push blocker for Phase 0.**

---

## Threat model notes (branch-specific)

| Threat | Status on this branch |
|--------|------------------------|
| Secret commit | Guard + pattern scan clean |
| Malicious skill/script ship | No new skills/scripts in Phase 0 tip |
| Fleet auto-deploy | Not enabled; plan forbids wiki fleet; existing wave still approval-gated |
| Prompt injection via research memo | No instruction-override markers; memo is operator policy |
| MCP / HTTP surface | Unchanged |
| License / credentials in tree | None introduced |

---

## Pre-push checklist

- [x] Secrets guard clean on `origin/develop...HEAD`  
- [x] Session security sweep PASS (active app)  
- [x] Malware lint clean  
- [x] Phase 0 defaults fail closed (`mode: off`)  
- [x] No dep / form changes requiring app security checklist  
- [ ] Push (operator) — recommended after optional commit of this report  
- [ ] PR: target `develop` (or intended base); do not merge with `--no-verify`  

---

## Recommendation

**Push is allowed from a security standpoint.**

Suggested push:

```bash
git push -u origin feature/llm-wiki-phase0-2026-07-15
```

If the PR should be **Phase 0 only** against a cleaner base, note that this branch tip also carries prior `work-2026-07-15` EOD/session-security-sweep commits vs `develop`; that broader delta is still security-clean per this audit.

---

## Related

- Plan: `reports/research/llm-wiki-karpathy-plan.md`  
- CONCERNS §13 mitigations  
- Session sweep: `reports/security/session-sweep-2026-07-15.md`  
