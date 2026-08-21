---
name: session-context-envelope
description: "Fixed-size session spin-up for any platform."
argument-hint: "[--compact | --json | --expand | --with-security-run]"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - bash
  - read_file
---
# Session context envelope (all platforms · all apps)

**Purpose:** One script = full spin-up awareness at low tokens. Critical: **user can pick up where they left off** (if they wish) and see version/base drift.

## THIS SURFACE IS GROK — use `.grok/` only for skills

| Host | Primary tree |
|------|----------------|
| **You (Grok)** | **`.grok/`** · manifest `.grok/project-manifest.yaml` · skills `.grok/skills/` |
| Claude | `.claude/` — do not use as primary |
| Copilot | `.github/` / `.copilot/` — do not use as primary |
| Gemini | `.gemini/` — do not use as primary |
| Cursor | `.cursor/` — do not use as primary |

Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`. Full map: `docs/reference/platform-surfaces.md`.

## Run (mandatory first tool call on `/chain session-start`)

**Preferred (token-efficient one-shot):**

```bash
python3 scripts/session-spinup-bundle.py
# Print only: reports/sessions/spinup-latest.txt
```

**Equivalent split:**

```bash
python3 scripts/session-context-envelope.py --write
# situation is included; later: session-situation-brief.py --use-cache
```

**Internal order (do not reverse):** `git fetch` → switch/pull **`remote_last`** (team tip) when clean →
**then** resume check/card → **situation** (vault/wiki/in-flight/repetition). Card before switch is wrong.

**Token rule:** do not re-dump vault JSON + wiki JSON + situation JSON separately after spinup.

## Agent rules (hard)

1. Print the **compact** CTX block verbatim. Do **not** restate it as a long blog post.
2. **Use surface root from CTX** (`surface platform=… root=…`) — for Grok that is **`.grok`**. Do not open `.claude`/`.copilot` skills as your procedure source.
3. **Always surface check + resume card** — from **post-switch** tree (even if stale). Missing card → note it; full session-start.
4. **Auto-switch to `remote_last`** (default `--write` applies `resume-branch.sh --apply`).  
   Clean tree → switch/pull. Real WIP → **block** (never discard); session spin-up noise only is soft-dirty.
5. When `on_remote_last=no` — surface **align** recommendations (status vs tip; how to rejoin). Staying off tip is intentional only.
6. When `resume_first=yes`, treat open/next on the envelope as authoritative (no full TODO re-read). Requires Branch match.
7. When `behind_develop>0` or `base:` is set — warn before release/version work; offer merge/rebase of `origin/develop`.
8. When `ver=` is present, cite template version (must match intended release base).
   When `ver_open drift=yes`, print `ver_ask` and wait for **retarget | keep**. Do not rewrite TODO/resume until the operator accepts.
9. `identity≠ok` → do not trust stack/runtime.
10. `mcp_policy=dev_only` — never start MCP on public hosts; expand `mcp_start` only if needed.
11. Do **not** Read full standup skill prose when envelope is enough.
12. Cite `reports/sessions/context-latest.json`.
13. Surface **`ws primary=…`** when present (multi-workstream registry; max 5 ids). Use `/multi-workstream` or `python3 scripts/workstream.py list` — do not dump full YAML.
14. **session-end / eod-shutdown** must leave a rich card that reminds next start of this order.

## Branch + card semantics (every app)

| Field | Meaning |
|-------|---------|
| `remote_last` | Newest `origin/*` work branch (excludes develop/master) |
| `switch applied/result` | Auto-switch outcome (`already_on` / `switched` / `pulled` / `blocked_dirty`) |
| `pickup offer=yes` | Need operator attention (dirty block, failed switch, or fresh card) |
| `last=` | Vault `operator_last_branch` (cross-machine pointer) |
| `target=` | Continue target (prefer `remote_last`) |
| `ask:` | Exact prompt to show the user |

## Platforms

Same command: **.grok** · **.claude** · **.copilot** · **.github** · **.gemini** · **.cursor**.

Token budget: `docs/reference/session-context-token-budget.md`.
