---
description: Decompose a complex, multi-faceted request into a token-efficient plan (single-lane or multi-lane parallel) and coordinate specialist subagents.
argument-hint: <high-level request, e.g. "Implement profile feature with avatar upload via Flask resizer">
allowed-tools: Task, Read, Grep, Glob, Bash
---

Invoke the `orchestrator` subagent with the following request:

$ARGUMENTS

The orchestrator must:
1. Read `.claude/project-manifest.yaml` first.
2. Run the cache-first load (see `.claude/commands/load-cache.md` logic).
3. Sync with the active TODO file.
4. Choose Shape A (single-lane) or Shape B (multi-lane parallel) per the rules in `.claude/agents/orchestrator.md`.
5. For discovery-heavy requests (unfamiliar domain, greenfield feature, docs overhaul), set `discovery_mode: true` in the JSON plan to prepend a perspective pass (`patterns/perspective-guided-discovery.md`) before lanes/steps.
6. Output the JSON plan + the mandatory "What Happens Next" section.
7. Auto-execute Step 1 and Step 2 (or independent lanes with `depends_on: []`) unless they are `high` risk or listed in `human_approval`.
