# Loop State (durable spine)

Updated by loop runs and `/loop-triage`. The model forgets; this file does not.

## Cache used (last run)

- `.github/project-manifest.yaml`
- `docs/codebase/INTEGRATIONS.md`, `LOOP.md`
- `STATE.md`, `loop-budget.md`
- `.github/workflows/` (10 files, names only)
- `reports/loops/2026-06-29-github-ci-host.md`

## Cache misses

- None recorded.

## Stale flags

- **fresh** — app-compound-gate 2026-07-11 (branch `develop`)

## Open (loop queue)

- [x] Beta-ready dry-run (`beta-ready-checklist.prompt.md`) — PASS 2026-06-17
- [x] Confirm prompt/agent name alignment post-sync (CONCERNS §1) — PASS 2026-06-17
- [x] Weekly L1 watches registered: cache-freshness, chain-health, github-ci, repo-health (`loop-weekly-watch.yml`)
- [x] First `repo-health-watch` run 2026-06-29 — verifier PASS
- [x] `cache-freshness-watch` 2026-06-29 — verifier PASS
- [x] `chain-health-watch` 2026-06-29 — verifier PASS (audit 100/100)
- [x] `github-ci-watch` 2026-06-29 — verifier PASS (CI green; 0 recent failures)
- [x] **Monday watches complete** 2026-06-29 (all four)
- [x] PR #72 merged 2026-06-29 — `develop` → `master` @ `cf3cfc5`
- [x] loops-starter wave deploy + commit-push: lightstone, e-ndsign, ndestates-io (2026-06-29)
- [x] run-chain-host smoke-test `cache-freshness-watch` (2026-06-29)

## Done (recent)

- [x] 2026-07-16 EOD: AI content guardrails on `feature/ai-content-guardrails-2026-07-16`; session-resume on master; bundle-hash stamp regenerated
- [x] 2026-07-15 LLM Wiki 0–4 → develop #151 → master #152; 4-app per-app rollout
- [x] 2026-07-11 Port #117 residual (npm package + licensing_policy) onto feature branch; vault+STATE spine
- [x] L1 daily-triage 2026-06-17; verifier PASS → reports/loops/2026-06-17-triage.md
- [x] Run `bash scripts/chain-audit.sh` in CI (`chain-audit.yml`)
- [x] `/read-codebase` cache refresh 2026-06-16 (`docs/codebase/*`, INDEX, repo memory)
- [x] Loop engineering foundation scaffolded (LOOP, STATE, budget, run-log)
- [x] Merge `feature/loop-daily-triage-l1` → `develop` (PR #2)
- [x] Run first L1 daily-triage; `loop-verifier` PASS (2026-06-16)
- [x] Commit triage artifact + STATE/run-log; fresh TODO `2026-06-16_TODO.md`
- [x] Chain skill merged → `develop` (PR #5) → `master` (PR #6)
- [x] Branch promotion workflow repaired and passing
- [x] `repo-health-watch` L1 2026-06-29; verifier PASS → reports/loops/2026-06-29-repo-health.md
- [x] PR #74 merged — Phase A/B chain automation on `develop`
- [x] `cache-freshness-watch` L1 2026-06-29; verifier PASS → reports/loops/2026-06-29-cache-freshness.md
- [x] `chain-health-watch` L1 2026-06-29; verifier PASS → reports/loops/2026-06-29-chain-health.md
- [x] `github-ci-watch` L1 2026-06-29; verifier PASS → reports/loops/2026-06-29-github-ci.md

## Verified facts

- Installer distribution (2026-07-11): pip (`pyproject.toml`), npm (`@ndestates/orchestrator`), Windows `install.ps1` (-Cli/-Npm), bash `install.sh` (--cli/--npm). Per-app only; fleet wave blocked.
- Cache-first is mandatory for all loops (`token_policy.mode: lean`).
- L1 daily-triage does not read application source or auto-fix.
- Promotion pipeline: `feature/*` → `develop` → `master`.

## Lessons → skills

- **mcp-threat-scan + rg (2026-07-26):** Never use `rg -I`/`--no-filename` in fail-closed scanners — paths are required for allowlist and vendor exclude; CI installs rg and would false-CRIT on self-hits. Regression: `tests/test_mcp_threat_scan.py`.
- **In-app install vs host package (2026-07-26):** Host CLI (uv/npm/pip) persists across branches; in-app `.grok`/chains do not unless `orchestrator/installed` + post-checkout (`install-persist`). Branch-sync must be **stdlib** (apps have no `orchestrator_cli` import). Versioning: three clocks — host / template / app lock — `orchestrator version`; never offer app `init` on template source when CLI is bundled.
- **In-app upgrade tokens (2026-07-26):** Agent-mediated `upgrade` is a mega-diff; prefer shell + compact summary; do not re-read full skill trees after upgrade.
- **No cozy workspace (2026-07-25):** CS experts and lawyers who believe “nobody can invade *our* tree” are the failure mode we design against. Treat professional/legal/internal content as DATA; comfort → tighten scans/guards, never skip. Doctrine: `docs/internal/SECURITY-POSTURE.md` §0; agent policy: `.grok/references/ai-content-guardrails.md`.
- **Wave upgrade bootstrap (2026-07-14):** Never write an untracked `.orchestrator-version` then run `git clean -fd` before `orchestrator upgrade` — clean deletes the lock and upgrade fails with “not installed”. Prefer `init` when lock missing, or commit lock first. Fleet wave remains stopped unless explicit approval.
- Vault integrity watch first run: ledger verifies clean at 52 events; host script + brief pair is enough for L1 (no source tree).
- MCP `get_chain_detail` may lag until chain is on the branch MCP serves — run chain from repo registry when scaffold is local-only.

- orchestrator: session-start compound gate (scaffold) — cache fresh on `develop` (scan 2026-06-23); durable lessons in STATE prevent loop context drift.

- **Vault at session-start (2026-07-11):** Always run `python3 scripts/session-vault-brief.py` during standup. `workspace_pointer` ≠ brain. Cite recent lessons; never re-plan vault-recorded done work.

- **Installer truth (2026-07-11):** PR **#116** on `develop` already shipped cease-fleet-default, `install.sh`/`install.ps1`, per-app `init`/`upgrade`, license-server. Do **not** report those as missing. Residual was **npm** (`package.json`, `bin/orchestrator.js`, `scripts/npm/*`) + `licensing_policy`/`first_party` from #117 branch — ported on `feature/draft-pr-hygiene-per-app-upgrade-2026-07-11`. Never merge #117 as-is (hard-deletes wave; dropped license_server). Fleet = deprecated/fail-closed; user installs per app (pip | npm | Windows).

- Full `.codebase-scan.txt` can lag README `[UPDATED]` markers; pair freshness check with targeted doc refresh after large merges.

- Chain opt-out menu prevents forced multi-step runs when user prefers single skill.
- Wave deploy must use `--commit-push`; gitignored scaffolds are skipped during commit (eod-shutdown 2026-06-29).
- Compound learning (steps 10–14) closes via `loop-compound.sh` after verifier PASS.

## Compound queue

| Target | Lesson | Status |
|--------|--------|--------|
| skill | MCP `get_chain_detail` may lag until chain is on the branch MCP serves — run cha | pending |

## Last chain run

- **When:** 2026-08-01T19:41:31Z
- **Chain:** eod-shutdown
- **Branch:** feature/work-2026-08-02
- **Outcome:** PASS
- **Steps:** —
- **Cache cited:** TODO/2026-08-01_TODO.md,TODO/2026-08-02_TODO.md,CHANGELOG.md,extensions/vscode-orchestrator/INSTRUCTIONS.md,reports/sessions/resume-2026-08-01.md
- **Artifact:** reports/sessions/resume-2026-08-01.md
- **Vault head (secure graph):** 484597356620 (reports/vault/events.jsonl)

## Last session

- **When:** 2026-07-18
- **Branch:** `feature/context-window-literacy-2026-07-18` (renamed from multi-session)
- **Outcome:** Multi-session **abandoned** (mailchimp only). Vector DB **abandoned** this initiative. PayPal **held**. Context-window literacy guide shipped.
- **Next:** PR docs → develop when ready; unhold PayPal only on explicit ask.