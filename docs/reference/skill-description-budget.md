# Skill description budget (Grok catalog injection)

**Status:** mandatory for orchestrator template and all deployed apps  
**Related:** `token_policy.skill_description_max_chars`, `scripts/lint-skill-descriptions.py`, `docs/reference/session-context-token-budget.md`

## Incident (why this exists)

On 2026-07-27 a Lightstone Grok session hit **~1.1M input tokens** and API budget errors (`Current message (~1.0M tokens) exceeds budget (~475k)`). Root cause was **not** a full codebase scan:

1. **Host injection** — Grok Build injects a synthetic `system_reminder` listing every discovered skill as `- name: <description>`.
2. **Re-injection** — that full catalog was appended **dozens of times** into durable chat history (same session: ~86 catalog messages, ~4.2 MB of skills text alone).
3. **Long descriptions** — many `SKILL.md` descriptions were 400–800+ characters of prose, inflating each injection (~50–55 KB per dump).
4. **Failed hard stop** — auto-compact failed; the agent continued instead of stopping at CRITICAL.

Prompt-cache **did** hit on re-reads; cache does **not** shrink history or stop re-injection.

## What Grok injects

Per [Grok skills docs](https://): skill **name** + **description** frontmatter are discovery metadata. The host lists them in-session. The skill **body** is loaded only when a skill is invoked.

Therefore:

| Field | Injected every turn (host) | Keep short? |
|-------|----------------------------|-------------|
| `name` | yes | yes (≤64 chars) |
| `description` | yes | **yes — ≤220 chars** |
| `when-to-use` | host-dependent | prefer short |
| body / references | no (on invoke) | full procedure OK |

## Policy

| Rule | Value |
|------|--------|
| `token_policy.skill_description_max_chars` | **220** (default) |
| Description content | One line: what it does + when to trigger. No essays. |
| Procedure detail | SKILL.md body only |
| Lint | `python3 scripts/lint-skill-descriptions.py` (exit 1 on violations) |
| Auto-fix | `python3 scripts/lint-skill-descriptions.py --fix` |
| After skill edit | lint, then `python3 scripts/sync_grok_to_github_claude.py` |

## Agent hard stop (complements description budget)

| Condition | Action |
|-----------|--------|
| context ≥ `hard_stop_context_tokens` (128000) | **STOP** — no tools; handoff + `/new` |
| auto-compact failed / API budget 400 | **STOP** — do not retry |
| context ≥ 100000 | WARNING — cache-efficient only |

`agent_stop_on_critical: true` in the manifest. Token-usage-meter CRITICAL is a **hard stop**, not a footer-only warning.

## Lint usage

```bash
# Report
python3 scripts/lint-skill-descriptions.py

# Rewrite long descriptions (YAML-safe quoted)
python3 scripts/lint-skill-descriptions.py --fix

# CI / pre-commit style
python3 scripts/lint-skill-descriptions.py --json
```

Canonical skills live under `.grok/skills/`. Sync copies to `.github/skills/`, `.copilot/skills/`, `.claude/commands/` as applicable.

## Host limitation (not fully fixable in-repo)

Re-injecting the full catalog into chat history on every turn is **Grok Build host behavior**. This template mitigates by:

1. Keeping each catalog line short (description budget).
2. Forcing agents to stop when context is CRITICAL.
3. Session-start lean path (envelope + resume card; no discovery loops).

If the host later supports "inject once" or "names-only index", prefer that and keep this budget.

## Verify after deploy to an app

```bash
python3 scripts/lint-skill-descriptions.py --root /path/to/app
# expect: Status: PASS
```
