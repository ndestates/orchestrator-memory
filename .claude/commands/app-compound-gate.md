---
description: Per-app compound learning gate for session-start: assess local loop spine (STATE, VISION, lessons-state), load durable lessons when READY, close SCAFFOLD or unclosed reports via loop-compound.
argument-hint: assess | close — default assess; close runs loop-compound when needed
allowed-tools: Read, Grep, Glob, Bash
---

# App Compound Gate (session-start)

**Per-app only.** Ensures this repository's loop spine is learning — not a fleet-wide audit.

## When to run

- Wired into `/chain session-start` step `compound-gate` when `LOOP.md` exists
- Manual: `/app-compound-gate` or `python3 scripts/app_compound_gate.py --json`

## Mandatory load (when `loop_enabled`)

Grep-before-read; section loads only:

1. `STATE.md` — `Lessons → skills`, `Stale flags`, `Compound queue`
2. `VISION.md` — standing spec (first section)
3. `reports/loops/lessons-state.json` — `app_lessons` count only (do not full-file unless closing)

## Assess

```bash
python3 scripts/app_compound_gate.py --json
```

| status | action | Agent behaviour |
|--------|--------|-----------------|
| `skip` | `none` | No `LOOP.md` — continue session-start |
| `ready` | `load_state` | Cite `state_lessons` in briefing; trust STATE over chat memory |
| `scaffold` | `close_compound` | Run `--close` (below) |
| `unclosed_report` | `close_compound` | Run `--close` on existing report |
| `gap` / `partial` | `offer_scaffold` / `offer_loops_starter` | **Report only** — offer `scaffold-loop-state.sh` / `loops-starter` deploy; human approves |
| `stale` cache (checker) | note in briefing | No auto `/read-codebase` at L1 |

## Close (SCAFFOLD or unclosed report only)

```bash
python3 scripts/app_compound_gate.py --close --json
```

Runs `loop-compound.sh` on the report. Updates `STATE.md` cache/stale sections and `loop-run-log.md` when writing a new gate report.

**Do not** run `--close` on `gap`/`partial` without human approval for scaffold/deploy.

## Anti-hallucination rule

When `ready`, treat `STATE.md` + `lessons-state.json` as authoritative for loop context. Do not invent prior loop outcomes from conversation history.

## L1 compliance

- No fleet `fleet-compound-audit.sh` in this skill
- No auto-fix on GAP (scaffold/deploy is human-gated)
- No source reads; checker + spine metadata only

See `patterns/compound-learning.md` and `patterns/app-compound-gate.md`.

User focus (optional): $ARGUMENTS
