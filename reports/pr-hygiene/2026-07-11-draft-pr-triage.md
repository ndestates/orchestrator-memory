# Draft PR triage — 2026-07-11

**Branch:** `feature/draft-pr-hygiene-per-app-upgrade-2026-07-11`  
**Base compared:** `origin/develop` @ `2124b11` (includes PR #116 installer/cease-wave)  
**Method:** `git cherry`, ahead/behind, `merge-tree` conflict markers, path sampling  

## Summary recommendation

| PR | Verdict | Action |
|----|---------|--------|
| **#117** | **KEEP — review, do not auto-merge** | Divergent hard-delete of fleet wave vs #116 fail-closed; Ollama BYOM; high conflict |
| **#112** | **PARTIAL — salvage or close** | Multi-ai branch mostly merged (`45ec0ff`); 1 leftover EOD+vault commit |
| **#101** | **CLOSE superseded** | Older multi-ai/claude EOD; behind 32; overlapping #100 |
| **#100** | **CLOSE superseded** | Subset of #101 path; wave-deploy-log EOD |
| **#94** | **CLOSE or extract** | Real docs/scripts but stale (68 behind, ~26 conflicts) |
| **#93** | **CLOSE superseded** | Pure EOD chore only |
| **#80** | **KEEP open — rebase** | Real feature; CI green; 112 behind / ~41 conflicts — rebase onto develop |

## Detail

### #117 `feature/stop-wave-autodeploy-installer-2026-07-08` → develop (DRAFT)
- **ahead 5 / behind 3** · tip not in develop · **0 cherry-equivalents** already on develop
- Unique commits include installer + **hard removal of fleet wave scripts** + Ollama host-only BYOM + EOD noise
- Would **delete 29 paths still on develop** (wave deploy scripts, policy, inventory, guards)
- Policy files **DIFF** vs develop: `wave-deploy-policy.sh`, `wave-inventory.yaml`, installation/licensing docs
- develop already has **#116** (`04723f2`) — cease fleet *default*, keep tooling, license-server, installers
- **~20 conflict markers** on merge-tree
- **Decision needed:** hard-delete fleet tooling (#117) vs fail-closed keep scripts (#116). Prefer #116 posture unless product wants total removal; if hard-delete wanted, re-apply as clean PR from develop without EOD commits.

### #112 `feature/multi-ai-best-practices-rollout-continued-2026-07-06` (DRAFT)
- develop already: `45ec0ff Merge feature/multi-ai-best-practices-rollout-continued-2026-07-06`
- tip **not** fully ancestor (1 unique: `4297ee3` EOD vault brain wiring, +979/−88, 28 files)
- Salvage candidates: `scripts/loop_compound.py`, `setup-vault-brain.sh`, vault helpers — only if not already evolved on develop
- Else **close as superseded** with comment pointing at `45ec0ff`

### #101, #100 (DRAFT)
- Shared commits (`58c148e`, `4c7818e`, `617b0eb`) — wave-deploy-log / token-meter EOD / compound gate notes
- #101 ahead 7 behind 32; #100 ahead 4 behind 32
- Multi-ai + claude deploy already on develop via later merges
- **Close both** as superseded

### #94 (DRAFT)
- 1 unique commit with real content: per-model manifests, `ensure-latest-db.sh`, safe-feature-development docs, resume-branch
- **~26 conflicts**, 68 behind — unsafe merge
- Extract missing files onto this hygiene branch if still valuable; else close

### #93 (DRAFT)
- 2 EOD commits only · **close**

### #80 `fix/wave-scaffold-before-commit` (open, not draft)
- Feature: repo-maintenance + security-pipeline watches
- Checks: chain-audit, decontamination, tooling-tests, GitGuardian — **SUCCESS**
- **112 behind**, **~41 conflicts** — rebase or recreate from develop
- Not draft; still hygiene-relevant

## Suggested close comments (for approval)

```
Superseded by later work on develop (incl. multi-ai merges / PR #116).
Triage: reports/pr-hygiene/2026-07-11-draft-pr-triage.md (2026-07-11).
Closing to reduce open draft noise. Re-open only if a unique commit must be recovered.
```

#117 special comment (if keeping draft open):
```
Held for product decision: this branch hard-deletes fleet wave tooling;
develop #116 fail-closes fleet but keeps scripts. Do not merge as-is —
rebase decision onto develop without EOD-only commits if hard-delete is desired.
```

## Out of scope this triage
- Actually closing/commenting on GitHub (needs operator approval)
- Merging or rebasing #80/#117
- Per-app upgrade policy code changes (item 2)

## Actions taken (2026-07-11)

Closed with superseded comments:
- #101, #100, #93, #94, #112

Left open:
- #117 (product decision: hard-delete fleet vs #116 fail-closed)
- #80 (rebase onto develop — CI green feature work)

## Port from #117 (2026-07-11)

**Branch:** `feature/draft-pr-hygiene-per-app-upgrade-2026-07-11`

Ported onto develop base (kept #116 license-server + fail-closed wave):

- `package.json` `@ndestates/orchestrator` + `bin/orchestrator.js` + `scripts/npm/*`
- `LICENSE`, pyproject license fields
- `src/orchestrator_cli/{defaults,first_party,licensing_policy}.py` + tests
- license/status/flow integration for entitlement policy
- `install.sh --npm`, `install.ps1 -Npm`, INSTALL.md + installation.md npm path

**Not** ported: mass wave script deletion, license_server removal, Ollama BYOM scripts.

**Spine:** STATE.md lesson "Installer truth (2026-07-11)" + verified fact.
**Vault:** lesson event `session:2026-07-11-port-117-npm-spine` (content_hash f330fd07fd1c1088).
