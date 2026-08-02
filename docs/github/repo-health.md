# Repository Health — EOD Checklist

[UPDATED 2026-07-07]

Date: 2026-06-29 (github-expert session: qa+skills to master + selective wave deploys) — refreshed for full docs alignment. See operations/delivery.md.

Scope: `ndestates/orchestrator` template — branch promotion, protected branches, EOD hygiene.

## Branch model

```
feature/*  --PR-->  develop  --PR-->  master
```

- `develop` and `master` are protected; direct push rejected.
- `branch-promotion-prs.yml` opens draft PRs `develop → master` after merges.

See main docs: operations/delivery.md and guides/knowledge-vault.md (vault events committed on EOD).

## EOD repo status checks (ddev-cleanup step 1)

| # | Check | Command / source |
|---|-------|------------------|
| 1 | Fetch latest | `git fetch origin --prune` |
| 2 | Current branch | `git branch --show-current` |
| 3 | Working tree | `git status -sb` |
| 4 | develop sync | `git rev-list --left-right --count origin/develop...develop` |
| 5 | master sync | `git rev-list --left-right --count origin/master...master` |
| 6 | Open PRs | `gh pr list --limit 10` |
| 7 | Recent merges | `gh pr list --state merged --limit 5` |
| 8 | Stale local branches | `git branch -vv` — delete merged `feature/*` |

## Recent delivery (2026-06-29 github-expert)

- Branch: fix/wave-scaffold-before-commit → PR #77 → develop → PR #76 → master (e8bd39b)
- Commit: 581353e feat(qa+skills) + follow-up sync + TODO
- Selective deploys (via deploy-template-wave.sh + internal commit): lightstone, e-ndsign, ndestates-io, google-stats (current feature branches on targets)
- New in rollout: qa-agent (8 wave specializations), skill-creator, prompt-patterns, webapp-testing, mysql-concurrency-test + full .grok/.github/.claude/.copilot syncs
- All guards passed (secrets, hooks, alignment 100/100 post-deploy)
- Untracked left (research only): reports/research/ports/

**github-expert enhancements (this session via /skill-creator + /prompt-patterns):**
- Added deep conflict/merge resolution expertise (detection, strategies for rebase/merge/PR/wave, prompt commands, rollback, verification with guards).
- Complementary prompt-patterns (grounded context extraction, Socratic coaching, strict tagged resolution output) + invocation hints when /github-expert used for git tasks.
- Updated agent.md, SKILL.md, prompt-patterns.md + TODO. Caches cited throughout.

## EOD branch reposition rule

**Do not leave the workspace on `master` or `develop`.**

After cleanup:

1. `git checkout develop && git pull origin develop`
2. `git checkout -b feature/<slug>-<tomorrow-YYYY-MM-DD>`
3. Next session starts on `feature/*`, ready for commits → PR → `develop`.

## Current snapshot (2026-06-28)

**Caches cited:** `docs/codebase/README.md` (promotion model), `docs/codebase/CONVENTIONS.md` (branch rules), `.grok/memories/INDEX.md`, docs/github/repo-health.md (self)

### Branch status

- **Current local branch**: `feature/selective-wave-rollout-control` (new feature for selective wave controls; uncommitted: updated repo-health.md and test_cli_flow.py with numbering/fix)
- **master (production equivalent)**: Latest 6363330 (merge #57 from develop). Open DRAFT PR #64 "chore(sync): promote develop to master" (Jun 24). Scheduled "Repository Sync & Maintenance" runs succeeding (latest 2026-06-28). Releases: v1.2.0 (Jun 21), v1.1.0, v1.0.1. Tags present. Protection: enforce_admins=true, dismiss_stale_reviews=true, required_reviews=0, no status_checks.
- **develop**: Latest df12e41 (merge #65 from feature/installer-cli-phase2). Open DRAFT PRs: #67 promote feature/gemini-claude-best-practices-rollout (Jun 27), #66 promote feature/installer-cli-phase3 (Jun 24). Recent promotion CI successful. Some older feature merges.
- **No production branch**: master serves production role (promotions land here + releases). No separate production branch found in remotes or GitHub.

### Recent work on this branch
- Selective wave rollout: updated deploy-template-wave.sh, commit-template-wave.sh, wave-inventory.yaml, docs to support choice (all/part/one/none/interactive) instead of automatic full rollout to wave apps.
- Multi-AI best practices integrated (grok_usage_guide.md, claude research, multi-ai prompt, .gemini support, tool/MCP).
- Test fix in test_cli_flow.py (added check= support to _git helper; numbered steps in multi-step tests for clarity).
- PR verification: reviewed #64/#66/#67; strategy: fix #66, merge #67 then #66 to develop, then #64 to master; use selective for waves.

### Open PRs summary
- To master: 1 open (promotion #64 DRAFT)
- To develop: 2 open (promotions #67 gemini-claude DRAFT, #66 installer DRAFT). Several recent merges.

### CI / Workflows
- Active: Branch Promotion PRs, Chain Registry Audit, Loop Daily Triage (L1), Loop Weekly Watch, MCP Security.
- Master recent: Repository Sync success x3 (scheduled). One Loop Daily Triage failure (Jun 26).
- No critical open issues or dependabot alerts (0).

### Divergence / Health
- develop...master: significant divergence.
- Current local: on feature/selective-wave-rollout-control (post multi-AI changes + selective wave).
- Working tree has local edits (docs + tests).
- Stale PRs and draft promotions noted.

### EOD / session checks (updated)
Use same as before + gh pr list, gh run list --branch master/develop, git rev-list counts.

**Note:** Selective wave control implemented to allow choosing rollout scope per run (all, specific apps, interactive, or none). See updated scripts/deploy-template-wave*.sh and docs/guides/template-deploy.md. Automatic full waves stopped for diverging apps.

## Related
- Skill: `.grok/skills/github-expert/SKILL.md` + `.grok/agents/github-expert.md`
- Promotion chains: see `chains/registry.yaml` (promote-master etc.)
- Wave: `scripts/wave-inventory.yaml`, `deploy-template-wave.sh` (now selective)

| Item | Status |
|------|--------|
| Local branch | `master` (at `ff735dc`, synced with `origin/master`) |
| `develop` | Synced with `origin/develop` at `20818da` |
| Working tree | Clean |
| Open PRs | None |
| Stale local features | `feature/loop-daily-triage-l1`, `feature/sync-grok-github-claude` (merged — safe to delete) |

## Related

- Skill: `.grok/skills/ddev-cleanup/SKILL.md`
- Conventions: `docs/codebase/CONVENTIONS.md` (branch flow)
- Workflow review: `docs/github/workflow-review.md`