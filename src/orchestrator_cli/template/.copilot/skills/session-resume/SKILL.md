---
name: session-resume
description: "Same-day return after session-end, and resume-first gate for session-start. Trust fresh resume card; skip redundant TODO/STATE reads."
argument-hint: "[check | read | write] · chain: .github/skills/chain/SKILL.md session-resume"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Session Resume

Two product surfaces (do not collapse them):

| Slash | When |
|-------|------|
| **`.github/skills/chain/SKILL.md session-resume`** | **Same calendar day** return after mid-day **`.github/skills/chain/SKILL.md session-end`** |
| **`.github/skills/chain/SKILL.md session-start`** | **New day** or after **`.github/skills/chain/SKILL.md eod-shutdown`** |

The skill also implements the **resume-first gate** used *inside* both chains.

Full rules: `references/resume-first.md`.

## Policy (hard)

| Moment | Requirement |
|--------|-------------|
| **session-end** | Write rich card (`--source session-end`); next command = **`.github/skills/chain/SKILL.md session-resume`** |
| **eod-shutdown** | Write rich card (`--source eod-shutdown`); next command = **`.github/skills/chain/SKILL.md session-start`** |
| **session-resume** | remote_last first → trust **session-end** card → lean security → work (no full standup) |
| **session-start** | remote_last first → check+card → security → lean cache → compound if needed |

**Product UX:** Operators reply with **numbered** next actions; pick a number. Extension + CLI use the same slashes.

## Same-day resume (`.github/skills/chain/SKILL.md session-resume`)

```bash
python3 scripts/session-context-envelope.py --write
python3 scripts/session-resume-brief.py check --json
bash scripts/session-security-sweep.sh   # active project only
```

When check JSON has:

| Field | Expect |
|-------|--------|
| `card_source` | `session-end` (or pause) |
| `same_day` | `yes` |
| `recommended_chain` | `session-resume` |
| `resume_first` | `yes` |

Then:

1. Print `card` verbatim (≤10 lines).
2. Honor `max_cache_files` (usually **0**).
3. Do **not** full TODO/STATE/VISION or daily-standup depth.
4. Security sweep + short open/next; **numbered** pick list.
5. If `recommended_chain=session-start` or `resume_first=no` → tell user to run **`.github/skills/chain/SKILL.md session-start`** instead.

## Gate (inside session-start)

```bash
python3 scripts/session-context-envelope.py --write
python3 scripts/session-resume-brief.py check --json
```

If check says `recommended_chain=session-resume` and user asked for session-start on a same-day pause card: **redirect** — “Use `.github/skills/chain/SKILL.md session-resume` for same-day return” (still land remote_last + show card).

When `resume_first=yes`:

1. Print `card` at top of briefing.
2. Skip full TODO/STATE/VISION; keep envelope, security, vault ≤2 events.
3. MCP dev-only.

## Write (session-end + eod)

```bash
python3 scripts/session-resume-brief.py write --rich --source session-end --summary "…"
python3 scripts/session-resume-brief.py write --rich --source eod-shutdown --summary "…"
```

## Response cap

Resume briefing: **≤80 words** after the card unless user asks for depth. End with **numbered** next actions.
