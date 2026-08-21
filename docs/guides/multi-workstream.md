# Multi-workstream (all platforms)

[UPDATED 2026-07-22]

**Purpose:** juggle several **work items** (active / held / parked) in one repo without N full chat sessions.  
Not a product demo framework. Tracks are whatever **you** register (feature work, holds, later PRs) — optional rows like WebMCP are unrelated betas, not required.

**One implementation for every LLM.**  
Canonical contract: **[IMPLEMENTATION.md](multi-workstream/IMPLEMENTATION.md)**  
Surfaces (Grok · Claude · Copilot · ChatGPT · Gemini · Cursor) are synced from that file:

```bash
python3 scripts/sync-multi-workstream-surfaces.py
python3 scripts/sync-multi-workstream-surfaces.py --check
```

**Operator UX = slash commands** (`/multi-workstream …`, `/chain session-start`).  
Scripts under `scripts/` are agent/CI runtime only.

## Overview

| Layer | What it is | Lifetime |
|-------|------------|----------|
| **Workstream** | Named track: branch + status + open/next + artifacts | Days–weeks |
| **Agent graph** | One-run diamond (fan-out → code reduce → synthesize) | Minutes |
| **Session** | One human↔agent conversation | Hours |

**Not this:** porting mailchimp multi-session Copilot SDK into the template.

## Before you begin

- Repo on a `feature/*` branch (or accept focus `--apply` checkout when clean)
- Python 3.10+ on PATH
- Optional: PyYAML (`python3 -c "import yaml"`) for `workstream.py` full commands

## Setup · alternatives · safeguards · worktrees

| Doc | Content |
|-----|---------|
| [setup.md](multi-workstream/setup.md) | Register, numbers, activate, diamond |
| [alternatives-and-safeguards.md](multi-workstream/alternatives-and-safeguards.md) | **serial vs diamond**, worktrees, integrity **guard** |

Commands: `add` · `activate` · `focus` · `diamond` · **`serial`** · **`guard`** · **`worktree`**.

## Guides per LLM

| You are… | Guide | Primary surface |
|----------|-------|-----------------|
| **Grok Build** | [Grok](multi-workstream/grok.md) | `.grok/skills/multi-workstream/` |
| **Claude Code** | [Claude](multi-workstream/claude.md) | `.claude/commands/multi-workstream.md` |
| **GitHub Copilot** | [Copilot](multi-workstream/copilot.md) | `.github/skills/multi-workstream/` · `.copilot/skills/` |
| **ChatGPT / Codex** | [ChatGPT](multi-workstream/chatgpt.md) | `.chatgpt/prompts/multi-workstream.md` |
| **Google Gemini** | [Gemini](multi-workstream/gemini.md) | `.gemini/prompts/multi-workstream.md` |
| **Cursor** | [Cursor](multi-workstream/cursor.md) | `.cursor/rules/multi-workstream.mdc` |

Map: [Platform surfaces](../reference/platform-surfaces.md).

## Operator commands (slash-first)

**Prefer slash / chain commands.** Scripts are what the **agent** runs underneath — not the primary operator interface (same pattern as `/chain session-start` → envelope script).

| Goal | Grok / Claude / Copilot-style | Chain |
|------|-------------------------------|--------|
| Session spin-up + **`ws`** line | `/chain session-start` | same |
| List tracks | `/multi-workstream list` | `/chain multi-workstream` |
| One-line brief | `/multi-workstream brief` | (included in chain) |
| Focus topology | `/multi-workstream graph` | (included in chain) |
| Set primary | `/multi-workstream focus <id>` | — |
| Primary + checkout if clean | `/multi-workstream focus <id> --apply` | — |
| Hold ready | `/multi-workstream hold <id> --ready` | — |
| Note next | `/multi-workstream note <id> --next "…"` | — |
| **Shape B recommend (safe multi-lane)** | `/multi-workstream diamond` | `/chain multi-workstream-diamond` |
| Inventory probe only | `/multi-workstream example` | `/chain workstream-graph-demo` (alias: `multi-workstream-demo`) |

ChatGPT / Gemini / Cursor: same names via that host’s multi-workstream prompt/rule (agent still runs the shared skill map).

Registry: `reports/sessions/workstreams.yaml`  
Reports: `recommend-latest.md` (Shape B) · `latest.md` (inventory probe)

### Recommended session flow (one command for parallel plan)

```text
/chain session-start
/multi-workstream diamond
```

You get a **recommendation only**: primary L0 + safe parallel lanes (e.g. docs + minor chores) + blocked held items.  
Nothing runs until you say e.g. **`approve parallel`**. Focus is never stolen from primary; held tracks stay frozen.

### Implementation map (agents / CI only)

```bash
python3 scripts/workstream.py list|brief|graph|focus|hold|note|diamond
python3 scripts/workstream_recommend.py
python3 scripts/workstream_graph_example.py
```

## Session-start (all platforms)

```text
/chain session-start
```

Look for a lean line like:

```text
ws primary=multi-stream-graphs active=1 held=2 parked=1 show=…
```

Max **5** ids in `show=`. Do **not** dump the full YAML unless you are editing tracks.  
Then optionally: `/multi-workstream diamond` for the Shape B plan.

## Example day (all hosts)

### 1. See what you are juggling

```text
/multi-workstream list
```

Example table:

| id | status | meaning |
|----|--------|---------|
| `multi-stream-graphs` | active (primary) | Current focus |
| `webmcp-beta` | active | Built; PR when ready |
| `opensource-license` | held_ready | Paused, resume later |
| `freemium-paypal` | held | Explicit unhold only |

### 2. Focus WebMCP without losing license state

```text
/multi-workstream focus webmcp-beta
/multi-workstream focus webmcp-beta --apply
```

License stays `held_ready` — no unhold.

### 3. Run a graph (not a linear chat)

```text
/multi-workstream example
```

or:

```text
/chain workstream-graph-demo
# alias: /chain multi-workstream-demo
```

### 4. Hold current work and switch primary

```text
/multi-workstream hold multi-stream-graphs --ready
/multi-workstream focus webmcp-beta --apply
```

### 5. End of session

Prefer `/chain session-end` or `/chain eod-shutdown` so the **resume card** and vault pointer survive. Next session-start will show `ws` again.

## Status meanings

| Status | Operator meaning |
|--------|------------------|
| `active` | May work on this track |
| `held_ready` | Paused with state frozen; unhold before expanding |
| `held` | Hard hold (e.g. PayPal production) |
| `parked` | Low priority; not primary |
| `done` | Closed |

## Rules (all LLMs)

1. **Primary surface only** for skill/command text (your tree). Shared: `scripts/`, `docs/`, `TODO/`, `reports/`.
2. **One primary focus** at a time; many tracks **tracked** in parallel.
3. **Never auto-unhold** license/PayPal.
4. **No multi-session SDK** port from mailchimp.
5. Graph **edges** prefer code reduce (`workstream_graph_example.py`) over stuffing N full caches into chat.
6. Token discipline: [Context-window literacy](context-window-literacy.md).

## Related

- Internal plan: `docs/internal/MULTI-WORKSTREAM-SESSION-V2-PLAN.md`
- Graph examples: [agent-graphs README](../examples/agent-graphs/README.md)
- Daily workflow: [daily-workflow.md](daily-workflow.md)
- WebMCP beta: [webmcp-beta.md](webmcp-beta.md)
