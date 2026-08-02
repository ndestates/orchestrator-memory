# Multi-workstream diamond recommendation (Shape B)

Generated: `2026-07-22T06:17:13.760563+00:00`
Primary focus (preserve): **`multi-stream-graphs`**
Auto-execute: **False** (recommend-only)
TODO source: `TODO/2026-07-22_TODO.md`

## One-command operator UX

```text
/chain session-start
/multi-workstream diamond
```

Or: `/multi-workstream recommend` · `/chain multi-workstream-diamond`

## Summary

- Candidates: 8
- Safe parallel: 1 (cap 4)
- Serial focus: 3
- Blocked (held/parked/high-risk): 4
- Lanes recommended: 2

## Recommended Shape B lanes

### L0-primary · risk=`serial_focus` · depends_on=[]
- **multi-stream-graphs** (workstream) — Multi-stream session + agent graphs
  - reason: heuristic from open/next/title
- contracts: primary progress note, no held-track edits

### L1-safe · risk=`safe_parallel` · depends_on=[]
- **todo-3** (todo) — Concrete vault/workstream graph example runnable
  - reason: heuristic from TODO open item
- contracts: diff limited to declared paths, no secrets, no branch checkout unless clean+approved

## Do not touch (blocked)

- **opensource-license** — Open-source Apache + Patreon + Pro license split (status=held_ready (do not expand without unhold/unpark))
- **freemium-paypal** — Freemium / PayPal production (status=held (do not expand without unhold/unpark))
- **webmcp-beta** — WebMCP beta (separate product — park unless working it) (status=parked (do not expand without unhold/unpark))
- **todo-4** — License track remains HELD READY (heuristic from TODO open item)

## Serial after / instead of parallel

- **todo-1** — Updated plan published (graph 14-step → orchestrator)
- **todo-2** — Workstream CLI + registry working

## Merge gates

**merge-primary-safe**
- [ ] Primary L0 still matches registry primary
- [ ] Safe lanes did not touch held/parked workstream ids
- [ ] No license/PayPal/prod files unless unhold
- [ ] Git status reviewable; no force-push

## Operator next

1. Review this recommendation (do not assume auto-run)
1. Approve safe lanes by saying: approve parallel
1. Keep primary: multi-stream-graphs
1. Held/parked stay frozen until explicit unhold

## Safety

- Does **not** unhold license/PayPal/parked tracks
- Does **not** auto-start subagents (recommendation only)
- Primary focus is always L0 — parallel lanes must not steal focus
- Prefer docs/chore/test in parallel; implement/refactor serial unless you override
