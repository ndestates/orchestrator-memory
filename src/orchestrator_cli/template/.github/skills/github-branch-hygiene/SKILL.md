---
name: github-branch-hygiene
description: "Safe remote/local branch prune: report-only default; --apply deletes merged origin refs. Never touches master/develop/staging/production. Use on prune remotes, stale branches."
argument-hint: "report | --apply | --apply --local | --include-dependabot"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
verified_at: "2026-08-20"
self_regulating: true
covers:
  - .github/skills/github-branch-hygiene
  - .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py
---
# GitHub branch hygiene

**Default is report-only.** Template skill so every orchestrator app can prune obsolete remotes safely.

Do **not** delete every `origin/*` that lacks a local branch of the same name. That removes other people’s feature branches.

## When to invoke

- User asks to prune remotes, clean merged branches, or tidy origin
- After merging a feature PR to `develop`
- EOD `.github/skills/ddev-cleanup/SKILL.md` when local merged branches linger
- `/github-expert` needs a branch-delete pass (delegate here)

## Protected (never delete)

`master`, `main`, `develop`, `staging`, `production`, `HEAD`, and the current checkout.

Template path: `feature/*` → `develop` → `master`. Apps may also use `staging` / `production` — those names stay protected.

## Procedure

### 1. Report (required first)

```bash
python3 .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py
python3 .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py --json
```

The script `git fetch origin --prune`s, then classifies each `origin/*` and local branch:

| Class | Action |
|-------|--------|
| Protected / current | keep |
| Head of an **open** PR (`gh pr list`) | keep |
| Ancestor of `origin/develop` (or staging/production/master) | **delete candidate** |
| Unmerged unique commits | keep |
| `dependabot/*` merged | listed separately until `--include-dependabot` |

### 2. Show the list. Do not delete yet.

If the user did not say “delete” / “apply” / “clean them”, stop after the report.

### 3. Apply (only with explicit user approval)

```bash
python3 .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py --apply
python3 .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py --apply --local
python3 .github/skills/github-branch-hygiene/scripts/github_branch_hygiene.py --apply --include-dependabot
```

`--apply` = `git push origin --delete` on remote candidates only.  
`--local` = also `git branch -d` (not `-D`) on local merged / no-upstream candidates.

### 4. Response format

```markdown
## Branch hygiene
- **Mode:** report | applied
- **Protected:** master, develop, staging, production
- **Remote candidates:** N (list)
- **Local candidates:** N
- **Kept open PR / unmerged:** N / N
- **Deleted:** … (if applied)
```

## Related (do not duplicate)

| Tool | Role |
|------|------|
| `/github-expert` | PRs, protection, promotion — delegates deletes here |
| `.github/skills/git-workflow-guardrails/SKILL.md` | Commit/push/PR gates |
| `.github/skills/ddev-cleanup/SKILL.md` | EOD; call this skill for merged-branch deletes |
| `/branch-context-agent` | Align work to the active branch — not a deleter |

## Anti-patterns

- Deleting remotes because they have no local clone
- `--apply` without showing the report first
- `git branch -D` / force-push
- Deleting `master` / `develop` / `staging` / `production`
- Mixing this with unrelated feature work on the same commit

## Self-regulation

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**Checks:** ran the script (did not guess); no `--apply` unless the user asked to delete; protected names absent from `deleted[]`.

```bash
python3 scripts/skill_health.py log --skill github-branch-hygiene --score 0.0-1.0 --notes "report|applied"
```
