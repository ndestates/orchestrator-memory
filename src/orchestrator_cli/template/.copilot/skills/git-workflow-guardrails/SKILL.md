---
name: git-workflow-guardrails
description: 'Git and githooks workflow for safe delivery. Use when committing, pushing, tagging, releasing, or preparing PR updates. Enforces: run security checklist before commit/push, run tests, commit only passing work, push branch, merge branch into develop, merge develop into master, and create annotated tags.'
argument-hint: 'Scope of change, branch name, and desired tag (if any)'
user-invocable: true
disable-model-invocation: false
---

# Git Workflow Guardrails

## Outcome
Produce a safe, auditable git delivery flow:
1. Security checks run before commit/push.
2. Relevant tests pass before commit/push.
3. Commit messages are clear and scoped.
4. Branch is pushed.
5. Completed work branch is merged into develop.
6. Develop is merged into master.
7. Next work branch is created and checked out.
8. Release or milestone tags are created and pushed when requested.
9. User receives progress updates through each major step.

## When To Use
- You are about to commit code changes.
- You are preparing to push a branch.
- You want a repeatable pre-push quality gate.
- You need a lightweight release-tag workflow.
- You want to enforce project security checks before commit/push.
- You want a standard branch completion workflow from feature/fix branch -> develop -> master.

## Inputs To Gather
- Branch name and branch intent.
- Target merge order and whether a PR-based merge is required by branch policy.
- Changed files and scope.
- Whether tagging is required for this push.
- Tag naming style (for example: vYYYY.MM.DD.N or semver).

## Team Defaults (Configured)
- Scope: workspace only.
- Tag format: semver (`vMAJOR.MINOR.PATCH`).
- Push gate: scope-based tests by default; full suite required for release/tag pushes.
- Agent behavior: must produce commit messages and keep user updated as work progresses.

## Workflow

### 1. Preflight
1. Confirm current branch is correct for the work.
2. Check repository status and staged/unstaged changes.
3. Ensure no unintended files are included.

Decision point:
- If unrelated files are present, stop and separate scope before committing.

### 2. Mandatory Security Gate (Before Commit and Before Push)

#### 2a. Secrets and env guard (required — blocks GitGuardian failures)
Before **every** commit and push, ensure hooks are installed and the guard passes:

```bash
bash scripts/setup-git-hooks.sh
python3 scripts/git-push-secrets-guard.py --staged   # before commit
# pre-push runs automatically: scripts/git-push-secrets-guard.py --range <remote>..<local>
```

The guard **blocks**:
- Live `.env` files (`.env`, `.env.backup`, `.env.production`, `.env.testing`, `.env.dusk`, `.env.local`, and unapproved `.env.*` variants)
- Dated `backup/20*.sql.gz` exports (live DB dumps with credentials; only `backup/latest-*.sql.gz` is allowed where applicable)
- `reports/flare-incidents/*.log` (generated 2FA/token noise)
- Common secret patterns in staged/pushed file content (GitHub/AWS/OpenAI tokens, private keys, JSON password literals)

Allowed env templates only: `.env.example`, `.env.production.example`, `.env.develop`.

Decision point:
- If the guard fails, **do not commit or push** — unstage/remove offending paths, rotate exposed secrets, re-run until green.
- Emergency bypass only with explicit audit trail: `GIT_PUSH_SECRETS_BYPASS=1 git push` (document reason in PR/commit notes).

#### 2b. Security checklist
Run (when the target app provides it):
- `ddev exec bash scripts/ci_security_checklist.sh`

Review generated artifacts under:
- `reports/security/`

Decision point:
- If new high-risk findings appear, stop and remediate first.
- If only known baseline advisories remain, document and continue.

### 3. Mandatory Test Gate + Workflow Pre-Check
Run relevant tests for changed scope.
Default gate:
- Scope-based tests for regular commits/pushes.
- Full suite for release or tag pushes:
   - `ddev exec php artisan test --no-coverage`

**Workflow health (new for stopping continual CI failures):**
Before push, if you touched `.github/workflows/` or CI-related files:
- Run `bash .grok/skills/github-workflow-expert/scripts/workflow-validate.sh` on changed files (or all).
- Optionally run pre-flight via `/github-ci-readiness-expert` or the ci-branch-readiness chain.
- If any workflow references new secrets, ensure they are set (gh secret list) before push.

Decision point:
- If tests or validation fail, fix issues and re-run until green.
- Do not commit failing code unless explicitly instructed by owner and clearly annotated.

After push:
- Immediately inspect first run(s): `gh run list --limit 5 --branch $(git branch --show-current)`
- If failure appears: use `/github-workflow-expert "diagnose the latest failure for <workflow-name>"` (it will run the diagnose-failure.sh script, analyze logs, list exact root cause + fix commands/edits).
- Fix using github-workflow-expert (edit + gh secret commands) then guardrails re-push.
- Goal: zero "continual failures" — diagnose + fix loop must be fast and developer-friendly.

### 4. Commit Preparation
1. Stage only intended files.
2. Re-check `git status --short`.
3. Write and present a precise commit message to the user before commit:
   - `type(scope): short summary`
   - Include why, risk notes, and validation summary in body when needed.

Commit execution rule:
- The agent must generate the exact commit message text and use it when committing.

Recommended commit body checklist:
- What changed.
- Why it changed.
- Security checks run and outcome.
- Tests run and outcome.

### 5. Push Flow
1. Push branch to origin.
2. Confirm remote tracking branch exists and is up to date.

### 5a. User Progress Updates (Mandatory)
Provide concise updates before and after each major stage:
1. Before security gate starts and after it completes.
2. Before tests start and after results are known.
3. Before commit and after commit hash is created.
4. Before push/merge actions and after each completes.
5. Before tagging and after tag push.

### 6. Branch Completion Integration Flow
Run this sequence when work on the branch is complete.

1. Ensure branch is clean and already pushed.
2. Update local branches:
   - `git fetch origin`
3. Merge completed work branch into develop:
   - `git checkout develop`
   - `git pull --ff-only origin develop`
   - `git merge --no-ff <completed-branch> -m "merge(<completed-branch>): integrate completed work"`
   - Re-run security and test gates.
   - `git push origin develop`
4. Merge develop into master:
   - `git checkout master`
   - `git pull --ff-only origin master`
   - `git merge --no-ff develop -m "merge(develop): promote validated changes"`
   - Re-run security and full test suite.
   - `git push origin master`
5. Create and switch to next branch:
   - `git checkout develop`
   - `git pull --ff-only origin develop`
   - `git checkout -b <next-work-branch>`
   - `git push -u origin <next-work-branch>`

Decision point:
- If merge conflicts occur, resolve conflicts, re-run gates, and continue.
- If branch protection requires PR merges, create PRs in the same order (completed branch -> develop, then develop -> master).

### 7. Tagging Flow (When Requested)
1. Create annotated tag:
   - `git tag -a <tag> -m "<release note>"`
2. Push tag:
   - `git push origin <tag>`
3. Verify tag exists on remote.

Tag format policy:
- Use semver tags, for example `v1.4.2`.

Decision point:
- If tag already exists, stop and choose one:
  - increment to a new tag,
  - or explicitly replace (only with approval).

## Branching Logic
- Security fail => fix security issue -> re-run security -> continue.
- Test fail => fix tests/code -> re-run tests -> continue.
- Mixed-scope branch => split or isolate commits before push.
- Integration fail on develop/master merge => resolve conflict -> re-run mandatory gates -> continue.
- Tag requested but quality gates not green => reject tagging until green.

## Completion Criteria
- Secrets/env guard passed (`scripts/git-push-secrets-guard.py` + hooks) before commit and before push.
- Security checklist executed successfully before commit and before push (when applicable).
- Relevant scope tests passed, and full suite passed for release/tag pushes.
- Commit message produced by agent and commit created with that message.
- Branch pushed successfully.
- Completed work branch merged into develop and pushed.
- Develop merged into master and pushed.
- Next work branch created, checked out, and pushed with upstream.
- Tag created and pushed when requested.
- User received clear progress updates throughout.
- Validation summary recorded in PR/notes.

## Githook Enforcement (Required)
Install once per clone (or after template-deploy / pulling hook changes):

```bash
bash scripts/setup-git-hooks.sh
```

Hooks (`.githooks/` via `core.hooksPath`):
- `pre-commit`: `scripts/git-push-secrets-guard.py --staged` (+ optional app extensions via `scripts/ensure-git-secrets-hooks.sh`).
- `pre-push`: `scripts/git-push-secrets-guard.py --range` on every outgoing commit range.

Hook policy:
- Hook failures **must** block commit/push (no secrets, no live `.env`, no dated DB dumps).
- `GIT_PUSH_SECRETS_BYPASS=1` is the only supported emergency bypass — must be documented.

## Example Prompts
- "Use git-workflow-guardrails for this branch and prepare a safe commit/push."
- "Use git-workflow-guardrails and complete branch integration into develop and master, then create my next branch."
- "Run the guardrails workflow and tag this release as v2026.03.29.1."
- "Apply guardrails, but run only tests related to supplier and compliance changes."
