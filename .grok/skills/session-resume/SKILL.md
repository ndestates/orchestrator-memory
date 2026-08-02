---
name: session-resume
description: "Resume-first gate for session-start: when a fresh resume card exists, trust it for branch/done/open/cache and skip redundant TODO/STATE/git reads to save tokens."
argument-hint: "[check | read | write]"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Session Resume (check + card always)

Token-efficient cross-session handoff. Full rules: `references/resume-first.md` (same file under
`.grok/skills/session-resume/`, `.github/skills/session-resume/`, `.copilot/skills/session-resume/`).

## Policy (hard)

| Moment | Requirement |
|--------|-------------|
| **session-start** | Always **check** + surface **card** when present; auto-switch to `remote_last` when clean |
| **session-end** | Always **write rich** resume card (`--rich --source session-end`) |
| **eod-shutdown** | Always **write rich** resume card via `eod-vault-emit.py` (`--source eod-shutdown`) |

## Check (session-start — always)

```bash
# Preferred: envelope applies remote_last + embeds check
python3 scripts/session-context-envelope.py --write
# Explicit check (always print card when present, even if stale)
python3 scripts/session-resume-brief.py check --json
```

When `resume_first=yes` (fresh card):

1. Print `card` verbatim at the top of the briefing (≤10 lines).
2. Honor `max_cache_files` (usually **0**).
3. Do **not** Read full TODO, STATE, VISION, or re-narrate git WIP.
4. Keep: envelope (or `resume-branch.sh --apply`), security sweep, vault verify ≤2 events.
5. MCP is **dev-only**.

When `resume_first=no`: full session-start **and still print the card** if `card_present=yes`.

## Write (session-end + eod — mandatory rich card)

```bash
# Mid-day pause (also via session-end-checkpoint.py)
python3 scripts/session-resume-brief.py write --rich --source session-end --summary "…"

# EOD (also embedded in eod-vault-emit.py after clean git)
python3 scripts/session-resume-brief.py write --rich --source eod-shutdown --summary "…"
```

Rich card includes: branch/dirty, HEAD, remote-last, ver, behind_develop, open, next, done, cache caveat.

## Read (compact paste)

```bash
python3 scripts/session-resume-brief.py read --compact
```

## Response cap

Resume-first briefing: **≤80 words** after the card block unless user asks for depth.