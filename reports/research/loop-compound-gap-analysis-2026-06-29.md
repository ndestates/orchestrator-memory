# Loop Compound Gap Analysis — post steps 10–14 closure

**Date:** 2026-06-29  
**Branch:** `feature/monday-loop-watches-2026-06-29`  
**Audits:** `loop-audit.sh` READY (≥80), `chain-audit.sh` 100/100  
**Cache cited:** `VISION.md`, `STATE.md`, `patterns/compound-learning.md`, `scripts/loop_compound.py`, `reports/loops/lessons-state.json`, `scripts/deploy-bundle.yaml`

---

## Executive summary

Steps **10–14** of the 14-step loop roadmap are now **implemented on the orchestrator template**. Each L1 loop run has a contract (`## Lessons`), a compound script (`loop-compound.sh`), durable JSON (`lessons-state.json`), a standing spec (`VISION.md`), and objective gate recording. **Remaining gaps** are mostly fleet rollout, L2 promotion automation, and human comprehension-debt habits — not missing spine files.

---

## What was closed (steps 10–14)

| Step | Theme | Implementation | Gate |
|------|-------|----------------|------|
| **10** | State + spec | `STATE.md` template, `VISION.md`, `lessons-state.json` | Loaded every loop via triage/compound skills |
| **11** | Minimum loop + gate | Existing L1 loops + `loop-audit` / `chain-audit` in compound | Objective exit codes recorded in `gate_history` |
| **12** | No Ralph Wiggum | Verifier + script gates (not opinion-only) | `loop-verifier` requires Lessons section |
| **13** | Comprehension debt | Documented in `VISION.md` + compound skill | Human: diff review, no arch at L1 |
| **14** | Security tax | `security_gates` in manifest; secrets guard on wave commit-push | Human: 30-day skill audit |

### New artifacts

| Path | Role |
|------|------|
| `VISION.md` | Standing spec — read each loop run |
| `patterns/compound-learning.md` | On-demand pattern |
| `.grok/skills/loop-compound/SKILL.md` | Maker for compound closure |
| `scripts/loop_compound.py` | Lessons extract → STATE + JSON + gates |
| `scripts/scaffold-loop-state.sh` | Wave app spine bootstrap |
| `starters/loop-state/*` | Templates when STATE missing |
| `reports/loops/lessons-state.json` | Machine-readable `lessons_learned` + `gate_history` |

### Workflow change

```
Loop run → report (## Lessons) → loop-verifier PASS → loop-compound.sh → STATE + JSON + promotion queue
```

---

## Maturity scorecard (14-step)

| Tier | Steps | Status |
|------|-------|--------|
| Unlock (1–4) | Loop vs prompt; cache spine | **Done** |
| Primitives (5–9) | Schedule, verifier, host workflows | **Done** (orchestrator) |
| Compound (10–14) | Lessons, gates, security/compression docs | **Done** (orchestrator template) |

**Template maturity:** step **14** design implemented at **L1** (human promotion queue; no auto CONCERNS/skill writes).

---

## Remaining gaps (orchestrator)

| # | Gap | Severity | Mitigation |
|---|-----|----------|------------|
| 1 | **Historical loop reports** lack `## Lessons` | Medium | Re-run compound with `none new` or backfill on next watch |
| 2 | **Promotion queue** is manual at L1 | Low (by design) | Enable L2 with allowlist when `allow_l2: true` |
| 3 | **CONCERNS / docs/codebase** not auto-updated | Medium | Human acts on `Compound queue` in STATE |
| 4 | **Memories INDEX** not auto-appended | Medium | Todo: `loop-compound --promote memory` at L2 |
| 5 | **Cost per accepted change** metric | Low | Track in `lessons-state.json` or token reports manually |
| 6 | **30-day security re-audit** | Low | Calendar reminder; not scripted |
| 7 | **Verifier** does not auto-invoke compound | Low | Documented in triage/verifier/run-chain-host |
| 8 | **chain registry** — compound not a scheduled chain | Low | On-demand skill sufficient at L1 |

---

## Remaining gaps (wave fleet)

| App | loops-starter | STATE/VISION scaffold | Compound tested |
|-----|---------------|----------------------|-----------------|
| orchestrator | n/a | **Yes** | **Yes** (cache-freshness sample) |
| lightstone | partial (`7aeb0c26`) | Custom STATE (stale) | **No** |
| e-ndsign | `569fc4a` | **No** — needs `scaffold-loop-state.sh` | **No** |
| ndestates-io | `1109e4d` | **No** | **No** |
| Other wave apps | not deployed | **No** | **No** |

**Fleet action:** Re-run `deploy-loops-starter-wave.sh` (updated bundle) + `scaffold-loop-state.sh` per app; one manual watch + compound per app.

---

## 4-condition test (per app)

| Condition | Orchestrator | Typical Laravel wave app |
|-----------|--------------|--------------------------|
| Task repeats | Yes (daily + weekly) | Yes if agent + CI active |
| Automated verification | Yes (audit scripts) | Yes if Pest/CI |
| Token budget | Managed (`loop-budget.md`) | Per-project |
| Senior tools | Skills + cache + gh | DDEV + tests when present |

---

## Recommended next steps (priority)

1. **Merge PR #75** — compound bundle lands on `develop`
2. **Wave delta** — redeploy `loops-starter` (compound files) to e-ndsign, ndestates-io, lightstone with scaffold + commit-push
3. **One ritual per app** — watch → verifier → `loop-compound.sh`; confirm `lessons-state.json` grows
4. **Process** — weekly review `Compound queue` in STATE; promote 1 item to CONCERNS or skill
5. **L2 design** (future) — `allow_l2: true` + allowlisted auto-promote to `docs/codebase/CONCERNS.md` only

---

## Verdict

| Question | Answer |
|----------|--------|
| Does the system learn each iteration? | **Yes on orchestrator** — lessons + gates persist |
| Is step 10–14 gap closed? | **Yes at template level** |
| Is learning automatic end-to-end? | **Partial** — capture/gate automated; CONCERNS/skill/memory promotion human at L1 |
| Biggest remaining risk | **Fleet spine drift** — wave apps without scaffold/compound run |