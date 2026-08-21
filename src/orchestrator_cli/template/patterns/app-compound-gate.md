# Pattern: App Compound Gate (session-start)

**Per-app only** — not `fleet-compound-audit.sh`.

## Purpose

At session-start in a loop-enabled repo (`LOOP.md` present), ensure:

1. Durable lessons in `STATE.md` are **loaded** (anti-hallucination)
2. Incomplete compound closure (**SCAFFOLD**, **unclosed report**) is **closed** in this repo
3. Broken spine (**GAP**) is **surfaced** with scaffold offer — no silent drift

## Cadence

- Every `/chain session-start` when `LOOP.md` exists
- Manual: `python3 scripts/app_compound_gate.py --json`

## Script

| Command | Role |
|---------|------|
| `scripts/app_compound_gate.py --json` | Assess local spine |
| `scripts/app_compound_gate.py --close --json` | Close via `loop-compound.sh` |

## Status key

| Status | Meaning |
|--------|---------|
| `skip` | No `LOOP.md` |
| `gap` | Spine broken (<4/7 files) |
| `partial` | 4–6/7 spine files |
| `scaffold` | Spine OK, no app-specific lesson |
| `unclosed_report` | Report has `## Lessons` not yet in `lessons-state.json` |
| `ready` | Spine + app lesson + gates |

## Chain wiring

`session-start` step `compound-gate` → skill `app-compound-gate` after `load`.

## Wave rollout

Ship via `loops-starter` bundle: skill, script, pattern, `app_compound_gate.py`.