# Bug Hunt Report — orchestrator upgrade → 1M+ token blow-up

**Date:** 2026-07-30  
**Mode:** deep / full  
**Branch:** `feature/eod-shutdown-2026-07-24` (HEAD)  
**Scope:** `orchestrator upgrade` + post-upgrade Grok session cost  
**Backup ID:** n/a (report-only; no patches applied)  
**Cache cited:** TODO/2026-07-26, docs/guides/per-app-upgrade.md, CONCERNS.md, commit `43f3977`, skill-description-budget design (on other branch)

## Executive summary

- **Confirmed bug (critical):** ~1M input-token sessions are real; root cause is **Grok skill-catalog re-injection** of long `SKILL.md` descriptions, not a full codebase scan and not primarily the upgrade CLI process itself.
- **How upgrade “goes wild”:** upgrade **deploys** the bloated catalog into the app (`.grok/skills/**`), so the **next** in-app Grok session multiplies long descriptions × skill count × dozens of re-injections → **~1.0–1.1M tokens** (matches 2026-07-27 Lightstone incident).
- **Fix already written** on `feature/skill-catalog-injection-budget-2026-07-27` @ `43f3977` — **not on current HEAD** and **not in deployed apps** (google-stats @ 1.9.5 still has 66/84 skills over 220 chars).
- **Secondary (high/medium):** upgrade CLI is agent-hostile (per-file line spam, no `--quiet`); `deploy-state.json` is 25–112 KB if agents `Read` it; policy field `skill_description_max_chars: 220` exists on HEAD without lint/enforcement.
- **Do not run P1 app upgrades inside long agent sessions** until description budget is merged + apps re-linted.

## Findings

| ID | Sev | Cat | Location | Summary | Status |
|----|-----|-----|----------|---------|--------|
| BH-001 | **critical** | performance / token | `.grok/skills/**/SKILL.md` + Grok host injection | Long skill descriptions re-injected every turn → ~1M tokens | open on HEAD; **fixed on `43f3977` (not merged)** |
| BH-002 | **high** | integration | `orchestrator upgrade` → app `.grok` | Upgrade ships bloated catalog; P1 upgrades spread the bug | open |
| BH-003 | **high** | process | template release vs branch | Policy `skill_description_max_chars: 220` on HEAD; lint script + short descs **absent** | open |
| BH-004 | **medium** | UX / agent | `scripts/_engine/deploy.py` | Per-file NEW/UPDATE/CONFLICT print (~25 KB dry-run; hundreds of lines); no upgrade `--quiet`/`--summary` | open |
| BH-005 | **medium** | token | `.grok/deploy-state.json` | 25–112 KB hash maps; agent Read dumps full state into context | open |
| BH-006 | **low** | docs/ops | TODO standing | “In-app upgrade is token-heavy — prefer shell” known but no hard guard | open |

---

### BH-001 — Skill catalog re-injection multiplies to ~1M tokens (critical)

- **Category:** performance / platform interaction  
- **Evidence:**

| Tree | Skills | Desc chars | ~tok/catalog | ×86 re-inject |
|------|-------:|-----------:|-------------:|--------------:|
| lightstone (app) | 92 | 47 181 | ~12 335 | **~1 060 810** |
| google-stats @ 1.9.5 | 84 | 28 017 | ~7 004 | ~602 k |
| orchestrator HEAD | 79 | 25 800 | ~6 450 | ~595 k |
| budget fix `43f3977` | 78 | 9 563 | ~2 390 | ~247 k |

  Documented incident (commit message + design doc on that branch): Lightstone Grok session **~1.1M input tokens**, API budget error `Current message (~1.0M tokens) exceeds budget (~475k)`, **~86 catalog messages**, **~4.2 MB** skills text. Cause: host injects `- name: <description>` for every skill and **re-appends the full list into durable history each turn**.

- **HEAD over-budget skills:** 61/79 descriptions **>220** chars (worst: qa-agent 797, docx 785, jersey-aml 704).  
- **Budget fix:** 0 over 220.

- **Impact:** Sessions become unusable; auto-compact fails; agent continues → cost explosion. Prompt-cache hits do **not** shrink history or stop re-injection.
- **Reproduction:**
  1. Open Grok Build in an app with upgraded `.grok/skills` (e.g. lightstone).
  2. Run multi-turn session (upgrade, review, more tools).
  3. Observe context / API budget climb to ~1M.
- **Fix (exists, not on HEAD):**
  - Cap descriptions at 220 (`scripts/lint-skill-descriptions.py` + `--fix`).
  - Docs: `docs/reference/skill-description-budget.md`.
  - Agent hard stop on CRITICAL / compact fail / budget 400.
  - CI + tests: `tests/test_lint_skill_descriptions.py`.
  - **Action:** merge/cherry-pick `43f3977` (or whole `feature/skill-catalog-injection-budget-2026-07-27`) → release → re-upgrade or lint-fix apps.
- **Tests:** present on fix branch; not on HEAD.

---

### BH-002 — Upgrade path spreads catalog bloat (high)

- **Category:** integration / deploy  
- **Evidence:** Dry-run on mailchimp (`orchestrator upgrade . --from-github v1.9.5 --no-pr`) is only **~25 KB / 444 lines / ~251 file events** — CLI alone is **not** 1M tokens.  
  After apply, apps receive full `.grok/skills` tree (~350–440 KB of SKILL.md bodies; descriptions inject every turn).  
  google-stats already at **1.9.5** still has **66 skills over 220 chars** → **upgrade to 1.9.5 does not fix the bug** because the budget fix is **post-1.9.5 / unreleased on this tip**.

- **Impact:** Running P1 “upgrade all apps to v1.9.5” **amplifies** token risk for every app session after upgrade.
- **Reproduction:** Upgrade clean app to 1.9.5 → open Grok in that app → multi-turn work.
- **Fix:**
  1. Ship description budget in a release **before or with** next app upgrade wave.
  2. After upgrade: `python3 scripts/lint-skill-descriptions.py --root <app> --fix` (once shipped).
  3. Prefer **host shell** for upgrade (TODO standing rule); agent only prints compact summary.
- **Tests:** upgrade flow tests exist; need assert on description budget post-deploy (suggested).

---

### BH-003 — Policy without enforcement on HEAD (high)

- **Category:** process / drift  
- **Evidence:** `.claude`/`.github` manifest includes `skill_description_max_chars: 220` and `hard_stop_context_tokens` / `agent_stop_on_critical`, but:
  - `scripts/lint-skill-descriptions.py` → **NO_LINT on HEAD**
  - `docs/reference/skill-description-budget.md` → only on `43f3977`
  - Descriptions still essay-length on HEAD

- **Impact:** Operators believe policy is live; apps and template still violate it.
- **Fix:** Land `43f3977` (or equivalent) on the release branch used for upgrades; wire lint into tooling CI / skill governance.

---

### BH-004 — Upgrade CLI verbose per-file output (medium)

- **Category:** UX / agent tool output  
- **Evidence:** `scripts/_engine/deploy.py` prints every `NEW` / `UPDATE` / `CONFLICT` / `SCAFFOLD` line (e.g. `print(f"NEW  {rel}")`).  
  `ensure` has `--quiet`; **upgrade/init do not**.  
  Dry-run mailchimp: **24 898 bytes**, **251** status lines.

- **Impact:** Not enough alone for 1M tokens, but agents that re-run upgrade, pipe full logs, or `git diff` after apply add large tool outputs on top of catalog re-injection.
- **Fix (suggested):**
  ```text
  orchestrator upgrade … --quiet     # stats-only
  orchestrator upgrade … --summary   # counts + report_path + branch
  ```
  Default for non-TTY or `ORCHESTRATOR_AGENT=1`: summary mode.
- **Tests:** assert quiet path line count ≤ N.

---

### BH-005 — Large deploy-state.json if agents Read it (medium)

- **Category:** token / agent behavior  
- **Evidence:** sizes on disk:

  | App | deploy-state.json |
  |-----|------------------:|
  | facebook-stats | ~25 KB |
  | google-stats | ~50 KB |
  | mailchimp | ~67 KB |
  | lightstone | ~86 KB |
  | ndestates-io | ~112 KB |

  Structure is per-file sha256 maps under `files` (not a compact lock).

- **Impact:** One mistaken `Read` of deploy-state ≈ 25–30k tokens; multiplies with other tool dumps.
- **Fix:** Agents: never full-read deploy-state; use `orchestrator check` / `.orchestrator-version`. Optional: compact state + sidecar for hashes.

---

### BH-006 — Known standing rule without mechanical guard (low)

- **Category:** process  
- **Evidence:** TODO standing: “In-app upgrade is token-heavy — prefer shell + compact summary”.  
  No skill hard-gate; agents still often run upgrade mid-session.
- **Fix:** Document in per-app-upgrade + orchestrator-deploy skill: **forbid** mid-session upgrade when meter WARNING/CRITICAL; shell-only + new session after.

---

## Weaknesses (non-bugs)

| ID | Area | Risk | Recommendation |
|----|------|------|----------------|
| W-001 | Grok host re-injection | Catalog re-appended every turn (host limitation) | Description budget + hard stop; lobby host for inject-once / names-only |
| W-002 | Full SKILL bodies on disk | ~100k+ tokens if agent Reads many bodies | Load only invoked skills; never bulk-read `.grok/skills` after upgrade |
| W-003 | `git add -A` commit after upgrade | Agent `git diff` of entire .grok can dump MBs | Post-upgrade: `git diff --stat` only |

## Root-cause chain (upgrade “goes wild”)

```text
Template ships long SKILL descriptions (HEAD: 61 over 220)
        ↓
orchestrator upgrade copies .grok/skills → app
        ↓
Grok Build injects name+description for every skill
        ↓
Host re-injects full catalog into history each turn (× tens–86)
        ↓
~50 KB catalog × 86 ≈ 4 MB ≈ ~1.0–1.1M tokens  (lightstone measured path)
        ↓
API budget error / unusable session
```

**CLI stdout of upgrade is a side channel (~25 KB), not the primary 1M mechanism.**

## Scan artifacts

- Dry-run log: `/tmp/upgrade-dry-mailchimp.txt` (24 898 bytes, 444 lines)
- Budget fix commit: `43f3977` on `feature/skill-catalog-injection-budget-2026-07-27` (**not ancestor of HEAD**)
- Design: `git show 43f3977:docs/reference/skill-description-budget.md`
- Measurements: this report (2026-07-30)

## Handoffs

- **security-audit-agent:** no (not auth/secrets)
- **test-specialist-agent:** yes — once lint lands, CI must fail long descriptions
- **project-drift-guardian:** yes — HEAD has policy field without enforcement (drift)
- **release:** block recommending P1 upgrades to 1.9.5 as “safe for Grok” until budget ships

## Next actions

1. **Merge/cherry-pick** `43f3977` (skill description budget + hard-stop docs/meter) onto the branch that will release next; cut tag **>1.9.5** (or patch release).
2. **Re-run** `lint-skill-descriptions.py --fix` on template + sync surfaces; CI gate.
3. **P1 app upgrades:** only from budget-fixed template; after upgrade run lint on app; prefer **shell outside agent**, then new session.
4. **Add** `orchestrator upgrade --quiet|--summary` (BH-004) — medium priority.
5. **Agent rule:** never `Read` full `deploy-state.json`; use lock/check only.
6. Until (1) lands: **do not** run multi-app upgrades inside Grok sessions expecting low token cost.

## Handoff (≤80 tokens)

```text
bug_hunt: 6 findings (1C/2H/2M/1L); fixed=0; tests=n/a
root: skill catalog re-injection (~1.06M @ lightstone×86); upgrade spreads bloat
fix_ready: 43f3977 skill-description budget (NOT on HEAD)
security_pending: none
next: merge budget fix before P1 app upgrades
```

## Fix log (2026-07-30)

| Finding | Action | Detail |
|---------|--------|--------|
| BH-001 / BH-003 | fixed (template) | Cherry-pick `43f3977` → `63c1a82` on `feature/eod-shutdown-2026-07-24` |
| BH-002 | partial | Apps still need upgrade from this tree (or in-app lint --fix once shipped) |
| BH-004 / BH-005 | open | Not in this cherry-pick |

**Verify:** `python3 scripts/lint-skill-descriptions.py` → PASS (79 skills, 0 over 220).  
**pytest:** `tests/test_lint_skill_descriptions.py` → 5 passed.  
**Catalog:** ~2.5k tok/injection (was ~6.5k); ×86 ~212k (was ~595k). VERSION **1.9.6**.

