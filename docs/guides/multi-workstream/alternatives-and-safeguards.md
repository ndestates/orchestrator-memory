# Alternatives to diamond + integrity safeguards

[UPDATED 2026-07-22]

## Alternatives to `/multi-workstream diamond`

Diamond is **one** planner (Shape B multi-lane *recommend*). You can use others:

| Mode | Command | When to use |
|------|---------|-------------|
| **Serial (safest)** | `/multi-workstream serial` | One primary only; no parallel lanes |
| **Diamond (balanced)** | `/multi-workstream diamond` | Primary + optional **safe** parallel (docs/tests/chore) |
| **Inventory only** | `/multi-workstream list` · `graph` · `example` | Status / health; no plan |
| **Worktree isolation** | `/multi-workstream worktree add <sel>` | Separate checkout per track (docs vs tests vs feature) |
| **Shape B orchestrator** | `/orchestrator …` multi-lane | In-request parallel agents with contracts (same tree unless worktrees) |
| **Manual PR lanes** | Human + CI | Real merge to develop/staging/master |

### Serial vs diamond vs worktree

```text
serial     → one focus, zero parallel recommendation
diamond    → recommend safe parallel *on current intent* (still no auto-exec)
worktree   → isolate branches in separate directories (no auto-merge)
```

Example day:

```text
/chain session-start
/multi-workstream guard
/multi-workstream serial          # or diamond
/multi-workstream worktree add 1  # isolate primary if needed
# work in main repo OR in the worktree path printed
# ship via PR — never auto-merge
```

---

## Workspaces (git worktrees)

### Commands

```text
/multi-workstream worktree list
/multi-workstream worktree add 1
/multi-workstream worktree add docs-polish
/multi-workstream worktree remove 1
/multi-workstream worktree status
```

Creates: `../{repo}-ws-{id}/` checked out to the workstream’s **feature branch**.

### Safeguards on worktrees

| Guard | Behaviour |
|-------|-----------|
| Held/parked | **Refuse** worktree unless `--force` |
| Protected branches | **Refuse** `master` / `main` / `develop` / `staging` / `release/*` |
| Path jail | Worktree only under **parent of repo** |
| No merge/push | Worktree tools **never** merge or push |
| Main dirty | `guard` warns (or fails with `--strict`) |

### Typical split

| # | Track | Worktree? | Work |
|---|--------|-----------|------|
| 1 | feature | optional | product code |
| 2 | docs | yes | markdown only |
| 3 | tests | yes | Pest/pytest only |
| 4 | scripts | yes | scripts/ only |

Still merge via **PR** when ready — multi-workstream does not land on develop/staging/master.

---

## Integrity safeguards (keep project on course)

### Always-on rules

1. **No auto-merge** to develop / staging / master / production.  
2. **No force-push** from multi-workstream commands.  
3. **No auto-unhold** of high-risk tracks (license, PayPal, prod).  
4. **Primary must be active** — `guard` fails if primary is held/parked.  
5. **Feature branches only** for worktrees.  
6. **Diamond/serial recommend only** — no auto-exec until operator approves.  
7. **Script-not-shell** — complex ops in `scripts/workstream*.py`, not ad-hoc shell.

### Run the guard

```text
/multi-workstream guard
```

Implementation: `python3 scripts/workstream_guard.py` (`--strict` if dirty main = FAIL).

| Exit | Meaning |
|------|---------|
| 0 | PASS |
| 1 | WARN (e.g. dirty main, high-risk active) |
| 2 | FAIL (primary held, protected branch, etc.) |

### Recommended session gate

```text
/chain session-start
/multi-workstream guard
/multi-workstream list
/multi-workstream prompts         # merge-ready / PR / WIP recommendations
/multi-workstream serial         # or diamond if you want parallel plan
```

If `guard` is FAIL → fix status/branch before worktree or parallel work.

### Merge-ready operator prompts

```text
/multi-workstream prompts
```

| Phase | User should understand |
|-------|------------------------|
| `merge_ready` | PR open + looks green/mergeable — **you** merge via gh/UI |
| `ready_for_pr` | Commits exist, no PR — open PR when ready |
| `pr_failing` / `pr_pending` | Fix or wait on CI |
| `wip` | Uncommitted work — commit first |
| `held` / `parked` | Frozen — activate only deliberately |

Multi-workstream **never** merges; it only **prompts and recommends**.

### What “broken by multistream” we prevent

| Risk | Mitigation |
|------|------------|
| Parallel edits collide | Prefer worktrees for different branches; diamond only for safe same-branch tasks |
| Accidental unhold of payments/license | activate is explicit; guard WARNs high-risk active |
| Work on develop/master in place | worktree refuses protected branches |
| Silent merge to protected | never implemented |
| Dirty main + checkout thrash | `focus --apply` and guard block/warn |

---

## Merge path (outside multi-workstream)

```text
feature work (main or worktree)
  → commit on feature/*
  → PR → develop (CI)
  → promote staging / master per project policy
```

Use `/git-workflow-guardrails` and existing branch-promotion workflows. Multi-workstream **tracks**; git/GitHub **lands** code.
