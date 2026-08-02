---
tools: ['search/codebase', 'execute/runInTerminal']
description: "Start a generic daily standup from cache, TODO, and branch status."
name: "Daily Standup Generic"
argument-hint: "Optional focus, e.g. 'security', 'ci', 'docs'"
agent: agent

---

# Daily Standup Generic

## Step 1: Load Cache (Lean)
Read in this order:
1. `.github/project-manifest.yaml`
2. `docs/codebase/README.md`
3. `docs/codebase/CONCERNS.md`
4. `docs/codebase/ARCHITECTURE.md`
5. Latest TODO file in `paths.todo_dir`

## Step 2: Branch and Worktree Snapshot
Run host-safe checks:
- Current branch name
- `git status --short`

## Step 3: Briefing
Output a short standup summary:
1. Current priority from TODO
2. Relevant concerns (by number)
3. Branch alignment with in-scope work
4. Immediate blocker, if any

## Step 4: Next Actions
End with exactly 3 numbered options for what to do next.

## Rules
- Keep response under 140 tokens.
- Cite every cache/TODO file used.
- Do not read source files until the user confirms direction.