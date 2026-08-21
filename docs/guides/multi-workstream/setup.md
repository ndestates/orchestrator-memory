# Multi-workstream setup

[UPDATED 2026-07-22]

How to **register tracks**, open them for work, and run a safe multi-lane plan.

**Ids** = workstream ids in `reports/sessions/workstreams.yaml` (not TODO line numbers).

Operator UX is **slash-first** (`/multi-workstream …`).

---

## 1. One-time (after pre-release install)

```bash
orchestrator upgrade /path/to/app --from-github v1.9.0-pre.5 --yes --no-pr
```

Confirm runtime CLIs landed (default `scripts` selection):

```bash
ls scripts/workstream.py scripts/workstream_worktree.py scripts/workstream_guard.py
```

On first use, ensure the registry exists. Template ships
`reports/sessions/workstreams.example.yaml` — copy to `workstreams.yaml` and edit,
or use `/multi-workstream add` below.

---

## 2. Session start

```text
/chain session-start
/multi-workstream list
```

CTX should show `ws primary=…`.

---

## 3. Register work items (ids)

Each real workstream needs an **id** (kebab-case):

```text
/multi-workstream add docs-polish --title "Docs polish" --status active --next "Finish guides"
/multi-workstream add api-hardening --title "API hardening" --branch feature/api-hardening --status held_ready
```

Or edit `reports/sessions/workstreams.yaml` (script-not-shell permanent path is the CLI).

Map TODO themes → ids yourself (diamond also invents temporary `todo-N` labels for recommendations only).

---

## 4. Numbers, ranges, and `all`

`/multi-workstream list` prints a **`#` column** (1, 2, 3, …) in list order.

| Selector | Meaning |
|----------|---------|
| `1` | First row |
| `2,3` | Second and third |
| `1-3` | First through third |
| `all` | Every workstream |
| `opensource-license` | Stable slug id (still works) |

```text
/multi-workstream list
/multi-workstream activate 2,3
/multi-workstream activate all
/multi-workstream focus 1
/multi-workstream hold 2 --ready
```

`focus` and `note` need **exactly one** target (`1` or a slug).  
`activate` / `hold` / `park` accept **many** or **all**.

## 5. Status lifecycle

| Slash | Status | Meaning |
|-------|--------|---------|
| `/multi-workstream activate <sel>` | `active` | Open for work (also **unhold** / **unpark**) |
| `/multi-workstream unhold <sel>` | `active` | Same as activate |
| `/multi-workstream hold <sel>` | `held` | Hard pause |
| `/multi-workstream hold <sel> --ready` | `held_ready` | Pause but resume-ready |
| `/multi-workstream park <sel>` | `parked` | Low priority / optional product |

**Diamond will not recommend work on held/parked/held_ready tracks.**

### Example: open three tracks for planning

```text
/multi-workstream activate 1,2,3
# or
/multi-workstream activate all
/multi-workstream list
```

Only do this if you **intend** to work those tracks (license/PayPal are high risk — unhold deliberately).

---

## 6. Focus (serial work)

One **primary** at a time for deep work:

```text
/multi-workstream focus 1
/multi-workstream focus 1 --apply
```

`--apply` checks out the branch when the git tree is **clean**.

Update next step:

```text
/multi-workstream note 1 --next "Polish diamond docs"
```

---

## 7. Safe multi-lane (Shape B recommend)

After statuses are set:

```text
/multi-workstream diamond
```

Read `reports/examples/agent-graphs/recommend-latest.md`.

- **L0** = primary (always)
- **L1+** = safe parallel (docs/chore/test heuristics)
- **Blocked** = still held/parked/high-risk keywords

Nothing runs until you say e.g. **`approve parallel`**.

---

## 8. Inventory graph (status only)

```text
/multi-workstream graph
/multi-workstream example
```

These **do not** implement work — they show topology / health.

---

## 9. Recommended daily loop

```text
/chain session-start
/multi-workstream guard
/multi-workstream list
/multi-workstream prompts
/multi-workstream diamond
# work primary (+ approved safe lanes only)
/multi-workstream note 1 --next "…"
/multi-workstream prompts
/chain session-end
```

### Merge-ready prompts

```text
/multi-workstream prompts
# same: /multi-workstream ready
# same: /multi-workstream status
```

Surfaces, per stream:

- **merge-ready** — open PR looks mergeable → review then `gh pr merge` (not multi-workstream)
- **ready_for_pr** — commits ahead, no PR → open PR when you are
- **wip** — uncommitted changes
- **frozen** — held/parked — activate only if intentional
- **Recommendations** — concrete next slash/git/gh steps

Report: `reports/examples/agent-graphs/prompts-latest.md`

---

## 10. “All 4 in the graph” setup

| Goal | Setup |
|------|--------|
| **See all 4** | Already — `list` / `graph` |
| **Work only primary** | Leave others held/parked (default) |
| **Work several as active** | `/multi-workstream activate <id>` for each you open |
| **Parallel safe bits** | activate only what is safe → `diamond` → approve parallel |
| **Full four features at once** | Not supported as four full sessions; activate + **serial focus** or narrow Shape B |

### Explicit open-all (operator choice)

```text
/multi-workstream activate all
/multi-workstream focus 1
/multi-workstream diamond
```

Then switch focus as you finish each:

```text
/multi-workstream hold 1 --ready
/multi-workstream focus 2
```

---

## Related

- [Hub](../multi-workstream.md)
- [IMPLEMENTATION](IMPLEMENTATION.md)
- Pre-release install: [multi-workstream-prerelease.md](../multi-workstream-prerelease.md)
