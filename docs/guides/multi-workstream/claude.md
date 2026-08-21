# Multi-workstream — Claude Code

[UPDATED 2026-07-22]

**You are Claude Code.** Primary tree: **`.claude/`** only.  
**Implementation is identical on all hosts** — see [IMPLEMENTATION.md](IMPLEMENTATION.md).  
Hub: [Multi-workstream (all platforms)](../multi-workstream.md).

| Use | Path |
|-----|------|
| Procedure | see IMPLEMENTATION §8 for this host |
| Shared runtime | `scripts/workstream.py`, `scripts/workstream_graph_example.py` |
| Registry | `reports/sessions/workstreams.yaml` |
| Do not use as primary | other `.platform/` trees |

## 1. Start the day

```text
/chain session-start
```

Expect CTX including `ws primary=…`. Answer `ask:` if present.

## 2. Day-to-day (slash — same as every model)

| Goal | Type |
|------|------|
| List tracks | `/multi-workstream list` |
| Brief | `/multi-workstream brief` |
| Graph | `/multi-workstream graph` |
| Set primary | `/multi-workstream focus <id>` |
| Primary + checkout | `/multi-workstream focus <id> --apply` |
| Hold ready | `/multi-workstream hold <id> --ready` |
| Note next | `/multi-workstream note <id> --next "…"` |
| Graph example | `/multi-workstream example` |
| Pack | `/chain multi-workstream` |
| Graph chain | `/chain workstream-graph-demo` |

## 3. Typical day

```text
/chain session-start
/multi-workstream list
/multi-workstream example
/chain session-end
```

## 4. Pasteable prompt

```text
Primary surface: .claude/ only. Multi-workstream implementation is shared (IMPLEMENTATION.md).
1) /chain session-start — print CTX including ws line
2) /multi-workstream list
3) Do not expand held / held_ready tracks unless I say unhold
4) On request: /multi-workstream example — summarize diamond reduce only
Never ask me to type python3 scripts/workstream.py as the main interface.
```

## 5. Agent implementation map

Identical on all hosts — [IMPLEMENTATION.md §2](IMPLEMENTATION.md).

## 6. Don’t

| Don’t | Why |
|-------|-----|
| Different commands per model | Contract is shared |
| Prefer raw python for operators | Slash-first |
| Unhold without ask | Policy |
| Multi-session SDK | Tracks ≠ N chats |

## Next

- [IMPLEMENTATION](IMPLEMENTATION.md) · [Hub](../multi-workstream.md)
