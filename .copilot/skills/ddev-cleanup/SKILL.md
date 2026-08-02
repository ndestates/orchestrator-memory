---
name: ddev-cleanup
description: "End-of-day cleanup for Grok Build + ddev projects."
argument-hint: "Optional summary for commit message, e.g. 'filament panel work done'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# ddev-cleanup

## Role

Perform a complete, clean shutdown of the current Grok Build + ddev project session. Enforce no project drift, verify GitHub/repo health, deliver via feature branches (never leave the workspace on `master` or `develop`), and ensure seamless resumption the next day.

## Activation

Use when the user says "end of day", "shutdown for today", "clean stop", "daily cleanup", "stop work", "push and shutdown".

## Branch policy (orchestrator template)

| Branch | EOD rule |
|--------|----------|
| `feature/*` | Commit/push here; may stay if work continues tomorrow |
| `develop` | **Never commit EOD changes directly** — create `feature/<slug>-YYYY-MM-DD` from `develop` first |
| `master` | **Never commit or remain here** — reposition to new `feature/*` from `develop` after cleanup |

Promotion flow: `feature/*` → PR → `develop` → PR → `master` (`branch-promotion-prs.yml`).

## Clean git rule (non-negotiable)

**EOD is not complete until the working tree is clean.** All session changes must be committed (or explicitly rejected and reverted). A dirty repo at shutdown is a failed EOD.

```bash
git status --porcelain   # must return empty before final verification
```

| State | Rule |
|-------|------|
| Modified tracked files | **Commit** on the correct feature branch (never leave unstaged) |
| Untracked intentional files | **Add and commit**, or add to `.gitignore` then commit that change |
| Scratch / temp files | **Delete** or gitignore — do not leave untracked clutter |
| Cannot commit safely | **Stop EOD** — report blockers; do not claim shutdown complete |

After commit and push, re-run `git status -sb` and confirm **nothing to commit, working tree clean** before repositioning for tomorrow.

## Procedure (run in order)

### 1. Repository status check (mandatory — `/github-expert` lite)

Activate `/github-expert` or run these checks from project root:

```bash
git fetch origin --prune
git branch --show-current
git status -sb
git rev-list --left-right --count origin/develop...develop 2>/dev/null || true
git rev-list --left-right --count origin/master...master 2>/dev/null || true
gh pr list --limit 10
gh pr list --state merged --limit 5
```

**Report an EOD repo status table:**

| Check | Expected | Action if fail |
|-------|----------|----------------|
| Working tree | **Clean** (zero porcelain lines) before EOD ends | Stage + commit all intentional work; never leave dirty |
| Current branch | Not `master` for new commits | Reposition (step 6) |
| `develop` vs `origin/develop` | In sync | `git pull origin develop` before new feature branch |
| Open PRs | None stale/blocking | Note in summary; user resolves tomorrow |
| Merged feature branches | Delete local stale | `git branch -d <name>` when merged |

Cache findings in session summary; update `docs/github/repo-health.md` when drift or recurring issues appear.

### 2. Enforce no project drift

- Activate `.github/skills/project-drift-guardian/SKILL.md` and `/branch-context-agent`.
- Align with active TODO and branch scope.
- Resolve drift before commit/push.

### 3. Branch gate before commit

If current branch is `master` or `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/<slug>-$(date +%Y-%m-%d)
```

- `<slug>`: short kebab from TODO objective or user hint (e.g. `loop-hardening`, `work`).
- Move any uncommitted work onto this branch before staging.

If already on `feature/*` with aligned scope, stay.

### 4. Stop ddev environment

- Run `ddev stop` (or `ddev poweroff` if no other projects active) when `.ddev/` exists.
- Confirm with `ddev list` or `ddev describe`.
- **Template repos without `.ddev/`:** skip and note N/A.

### 5. Update Grok Build artifacts

- Refresh project cache if applicable.
- Run `python3 scripts/sync_grok_to_github_claude.py` when `.grok/` skills or prompts changed.
- Update active TODO (today closed, tomorrow opened via `/todo-specialist-agent` when chained).
- Run `bash scripts.github/skills/chain/SKILL.md-audit.sh` when `chains/registry.yaml` changed.

**Record resume branch + rich resume card for session-start (mandatory — never skip):**

```bash
bash scripts/resume-branch.sh
python3 scripts/vault-workspace-pointer.py --emit   # per-operator last branch in vault brain
# Rich resume card is written by eod-vault-emit.py (step 9); if running cleanup alone:
python3 scripts/session-resume-brief.py write --rich --source eod-shutdown --summary "EOD cleanup"
```

Write into **tomorrow's** `TODO/YYYY-MM-DD_TODO.md` (after **Branch:**):

```markdown
**Resume branch (remote-last):** `<branch>` — `<date>` — `<subject>`
**Workspace target:** session-start auto-switches to remote_last when clean
```

- `.github/skills/chain/SKILL.md session-start` **auto-switches** to `remote_last` when clean and always runs check+card.

### 6. Git cleanup, commit all, and push (mandatory clean tree)

```bash
git status -sb
git add -A
git status -sb
# If git add -A staged nothing but porcelain still shows lines, resolve each path (commit, gitignore, or remove)
git commit -m "End of day cleanup: <summary>. No project drift confirmed."
git push -u origin "$(git branch --show-current)"
git status --porcelain   # must be empty — if not, fix and commit again before step 7
```

- **Commit every intentional change** from the session — no uncommitted tracked files.
- Use `git add -A` only after confirming no secrets or local-only artifacts belong in the repo.
- Open PR to `develop` when branch protection blocks direct push.
- Never push EOD commits to `master` or `develop`.
- **Do not proceed to step 7** while `git status --porcelain` is non-empty.

### 7. Reposition for tomorrow (mandatory if on `master` or `develop`)

After push (or when working tree is clean on a promotion branch):

```bash
git checkout develop
git pull origin develop
git checkout -b feature/<slug>-$(date -d tomorrow +%Y-%m-%d 2>/dev/null || date -v+1d +%Y-%m-%d)
```

- Use **tomorrow's date** in the branch name when creating the next-day branch.
- Leave the workspace on this feature branch — **not** on `master`.
- Empty branch: no push required until first commit tomorrow.

### 8. Final verification (clean git gate)

```bash
git status --porcelain && echo "FAIL: working tree not clean" && exit 1
git branch --show-current
```

- **Working tree must be clean** — `git status --porcelain` empty (required; EOD fails otherwise).
- Confirm last push succeeded (if any).
- Confirm current branch is `feature/*` (not `master`/`develop` unless reposition pending).
- Suggest tomorrow: `ddev start` (if applicable), `.github/skills/chain/SKILL.md session-start` (reads **Resume branch** from TODO + `scripts/resume-branch.sh`), active `TODO/YYYY-MM-DD_TODO.md`.

### 8b. Wiki file-back offer (Phase 2 — optional, never auto)

When `wiki_policy.mode` is `lean` or `full` and `wiki/index.md` exists:

1. Run `python3 scripts/session-wiki-brief.py` once for context.
2. **Offer** the operator 0–2 durable insights from today as:
   - `wiki/queries/YYYY-MM-DD-<slug>.md` via `/llm-wiki file-answer`, or
   - an open-question append (with approval)
3. **Do not** auto-write wiki pages at EOD. Skip when mode=off or user declines.

### 9. Emit learnings to vault graph (**guaranteed** — v1.5.0+)

**Mandatory final step.** EOD is not complete until the vault has been written (or the script fails loudly).

Execute exactly:

```bash
python3 scripts/eod-vault-emit.py
# optional richer summary:
# python3 scripts/eod-vault-emit.py --summary "Closed TODO-xxx, …" --area process
```

| Mode | When | What is written |
|------|------|-----------------|
| **Rich** | Changelog and/or commits today | `synthesis` + `lesson` + workspace pointer |
| **Heartbeat** | Quiet day | Minimal `lesson` so app vaults still grow |

- **Do not** use `--skip-if-empty` in normal EOD (that is legacy opt-out).
- Exit non-zero → fix vault scripts / `_engine` before claiming EOD complete.
- Query: `python3 scripts/_engine/vault_query.py --query "eod" --area process --hint`

**Apps:** same command after orchestrator ≥1.5.0 deploy (`scripts` selection).

## Idempotency

- Check before destructive actions (`git branch -D`, force push).
- If already on a suitable `feature/*` with clean tree, skip step 7.
- Safe to re-run; repo status step always runs.

## Chained use

Part of `eod-shutdown` / `eod-session` chain (`todo-specialist` → `readme-specialist` → `token-usage-meter` → `ddev-cleanup` → vault emit).

Repo status, **clean git**, branch reposition, and **vault brain contribution** (step 9) are owned by this skill.

The eod-shutdown chain now explicitly strengthens the integration by requiring the vault emit as the final action.

Run commands via bash tool. Always work in project root. Log each step.