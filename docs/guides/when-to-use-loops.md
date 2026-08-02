# When to use loops

[UPDATED 2026-07-11] — decision guide + scaffolded L1 candidates

## Overview

A **loop** is a system that re-prompts agents on a **schedule or goal** with durable memory (`STATE.md`, vault, lean cache). You design the loop once; agents execute inside it.

A **chain** is **on-demand** multi-skill composition with one shared cache load.

**Default level:** **L1** — cache synthesis → report → verifier → compound. **No auto-fix.**

## Decision table

| Situation | Prefer | Why |
|-----------|--------|-----|
| Repeats daily/weekly/on push | **Loop** | Schedule + host snapshot beat re-briefing |
| Need report + `STATE.md` update | **Loop** | Maker/checker + compound lessons |
| Cache + audits are enough | **Loop** | `max_source_files: 0` stays lean |
| One-shot feature / refactor | Branch + specialists | Not recurring health |
| Multi-skill right now | `/chain …` | Shared cache, no schedule |
| Session open/close | `session-start` / `session-end` / `eod-shutdown` | Chains, not loops |
| Deep product judgment | Human + experts | L1 forbids auto source deep-dives |
| Research / docs discovery | On-demand patterns | Not daily triage |

## Signals a loop is the right tool

1. **Cadence** — same question every Monday or every weekday.  
2. **Machine-checkable** — audit exit codes, `gh` status, freshness JSON, ledger verify.  
3. **Bounded blast radius** — report paths only; no merge, no fleet deploy.  
4. **Compound value** — lessons should not be re-planned next session (`/loop-compound` after verifier PASS).  
5. **Token discipline** — fits `loop-budget.md` and `max_cache_files_per_loop`.

## Signals a loop is the wrong tool

- Auth, payments, schema redesign, or anything needing L2 auto-PR without policy.  
- “Fix this bug once” — use `/bug-hunter` or a feature branch.  
- “Explain the architecture” once — `/acquire-codebase-knowledge` or docs specialist.  
- Fleet wave to all apps — blocked by default; use [per-app upgrade](per-app-upgrade.md).

## What already ships (active)

| Loop | Cadence | Job |
|------|---------|-----|
| daily-triage | Weekdays 09:00 UTC | Priorities from cache + TODO + CONCERNS |
| cache-freshness-watch | Mondays 09:30 UTC | Cache age / branch drift |
| chain-health-watch | Mondays 09:30 UTC | Chain registry audit score |
| github-ci-watch | Mondays 09:30 UTC | Recent CI failures |
| repo-health-watch | Mondays 09:30 UTC | Branch/PR hygiene |
| branch-promotion-watch | On push | feature → develop → master alignment |
| compound-learning | After verifier PASS | Lessons → STATE / vault |

Registry spine: [LOOP.md](../../LOOP.md) · patterns: `patterns/` · budget: `loop-budget.md`.

## Scaffolded candidates (manual first)

Registered in `patterns/registry.yaml` and documented under `patterns/` — **not** on the weekly cron until `loop-audit.sh` ≥ 80 and you enable a job.

| Pattern | Purpose | Manual entry |
|---------|---------|--------------|
| [vault-integrity-watch](../../patterns/vault-integrity-watch.md) | `verify_ledger` + growth/ISSUES report | `/chain vault-integrity-watch` |
| [version-drift-watch](../../patterns/version-drift-watch.md) | Template VERSION vs app locks (report only) | `/chain version-drift-watch` |

## Loop vs chain vs session

```text
Recurring health / hygiene     →  Loop (L1 + verifier + compound)
Ad-hoc multi-skill             →  /chain <id>
Open or close a working day    →  session-start | session-end | eod-shutdown
Ship a product change          →  feature/* branch + specialists
```

## How to add a loop safely

1. Write `patterns/<name>.md` (purpose, cache files, maker/verifier, L1 rules).  
2. Register in `patterns/registry.yaml` under `loops:` (or `patterns:` if on-demand only).  
3. Add a row to `LOOP.md` (mark **manual** until scheduled).  
4. Optional: chain in `chains/registry.yaml` (load → maker → verify).  
5. Optional host snapshot script under `scripts/loop-*-host.sh`.  
6. Run `bash scripts/loop-audit.sh` — target **≥ 80** before any schedule.  
7. Enable cron only with human approval; keep **L1** until `loop_policy.allow_l2`.

## Invocation cheat sheet

```text
# Existing daily
/loop-triage
/loop-verifier
/loop-compound

# Existing weekly (or scheduled allowlist)
/chain cache-freshness-watch
/chain chain-health-watch
/chain github-ci-watch
/chain repo-health-watch

# Scaffolded (this guide)
/chain vault-integrity-watch
/chain version-drift-watch

# Audit readiness
bash scripts/loop-audit.sh
```

## Related

- [Daily workflow](daily-workflow.md)  
- [Chains and skills](chains-and-skills.md)  
- [Knowledge vault](knowledge-vault.md)  
- [Per-app upgrade](per-app-upgrade.md)  
- Skill: `/loop-engineering`  
