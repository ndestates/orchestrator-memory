# /loop-engineering

> Loop engineering for this template: design systems that prompt agents, not hand prompts.

**Platform:** Cursor · same skill as Grok `/loop-engineering` · Claude `/loop-engineering`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `e.g. 'assess readiness', 'add PR babysitter loop', 'explain L1 vs L2`

# Loop Engineering (orchestrator template)

**Principle:** You design loops; agents execute inside them. **Cache is king:** every loop starts with manifest + lean cache — never source-first.

**Registry access:** `chains/registry.yaml` is 2000+ lines — **Grep** chain `id:` + section Read, or MCP `get_chain_detail` / `list_chains`. Never full-file Read.

## Stack in this repo

| Layer | Files |
|-------|-------|
| Registry | `LOOP.md`, `patterns/registry.yaml` |
| Memory | `STATE.md`, `loop-run-log.md`, `reports/loops/lessons-state.json` |
| Standing spec | `VISION.md` |
| Compound | `loop-compound`, `scripts/loop-compound.sh`, `patterns/compound-learning.md` |
| Budget | `loop-budget.md`, `token_policy` in manifest |
| Skills | `loop-triage`, `loop-verifier`, `chain`, `cache-efficient`, `load-project-cache-first` |
| Schedule | `.github/workflows/loop-daily-triage.yml` |
| Audit | `scripts/loop-audit.sh` |

## Maturity (14-step shorthand)

1–4 Unlock: loop vs prompt; cache + STATE as spine  
5–9 Primitives: `/goal` conditions, verifier, worktrees, schedule  
10–14 Compound: lessons → skills; eval gates; safety boundaries — **implemented** via `/loop-compound`, `VISION.md`, `lessons-state.json`

This template ships at **L1 daily-triage** plus **weekly watches** plus **compound closure** after verifier PASS.

## Start here

1. `/load-project-cache-first` or `/cache-efficient`
2. **When to loop:** human guide [docs/guides/when-to-use-loops.md](../../../docs/guides/when-to-use-loops.md) (vs chain/session)
3. `bash scripts/loop-audit.sh`
4. `/loop-triage` → `/loop-verifier` → `/loop-compound`
5. Read `patterns/daily-triage.md` and `patterns/compound-learning.md` before adding loops
6. Scaffolded manual: `/chain vault-integrity-watch`, `/chain version-drift-watch`

## Adding loops

- Register in `LOOP.md` + `patterns/registry.yaml`
- Set `cache_files_required` and `max_source_files`
- Default **L1** until `loop_policy.allow_l2: true` with human approval

## Perspective-guided discovery (on-demand)

**Not a loop.** Pattern: `patterns/perspective-guided-discovery.md` (registry `patterns:` section).

- Use for discovery, docs, or external research — **not** for bug fixes, migrations, or scheduled L1 triage.
- Entry: `/acquire-codebase-knowledge` Phase 1.5, `/documentation-specialist` Phase 2.5, `/chain research-deep-dive`, or `/orchestrator` with `discovery_mode: true`.
- L1 loops stay report-only; daily triage does **not** auto-run perspective pass or research chain.
- L2+ (future): optional `reports/research/*` memo → `STATE.md` — blocked while `loop_policy.allow_l2: false`.

## Related

- On-demand skill chains: `CHAIN.md`, `/chain` (shared cache, minimal handoffs)
- Token mode: `/cache-efficient`
- Skill development & measurement: `/skill-creator` (quantitative evals, subagent benchmarks, iteration for primitives that loops invoke). See reports/research/skill-port-plan.md for the port from external research.
- MCP quality: references in `mcp-server/reference/` (best practices + evaluation methodology).

User focus (optional): use any extra chat text as $ARGUMENTS.
