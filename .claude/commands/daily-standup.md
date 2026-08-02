---
description: Start a daily working session on project using the local cache + today's TODO + open concerns. This is the recommended prompt for almost every normal development or review session.
argument-hint: Optional focus, e.g. 'Frontend', 'Users', 'Filament resources', 'schema', 'tests', 'signing workflows'
allowed-tools: Read, Grep, Glob, Bash
---

# Daily Standup With Cache (Recommended Default Session Start)

**Invoke at the beginning of most sessions.** Canonical skill: `.claude/commands/daily-standup/SKILL.md`.

## Step 0: Resume-first gate (before cache reads)

```bash
python3 scripts/session-resume-brief.py check --json
```

When `resume_first=yes`: print `card` verbatim; **do not** Read full TODO/STATE/VISION; `max_cache_files` from check (usually 0). Rules: `.claude/commands/session-resume/references/resume-first.md`.

When `resume_first=no`: full standup (cache spine + TODO + vault).

## Step 1: Runtime + branch resume (always)

```bash
bash scripts/detect-project-runtime.sh
git fetch origin --prune
bash scripts/resume-branch.sh
```

Active-repo only — **do not** run `sync-all-projects.sh`. Offer branch switch; never auto-checkout.

## Step 2: Security + vault (lean when resume_first=yes)

- `bash scripts/session-security-sweep.sh` — cite report one-liner
- When `resume_first=yes`: vault verify + ≤2 events only
- When `resume_first=no`: full `session-vault-brief.py` + `session-vault-todo-query.py`

## Step 3: Cache load (skip spine when resume_first=yes)

Honor `max_cache_files` from check. Never Read `.codebase-scan.txt`.

User focus (optional): $ARGUMENTS
