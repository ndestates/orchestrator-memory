---
description: Template for handling a complex, multi-part instruction. Decomposes into small steps and delegates to specialists.
argument-hint: <paste full complex instruction>
allowed-tools: Task, Read, Grep, Glob, Bash
---

# Multi-Faceted Instruction Handler

**Full Requirement**: $ARGUMENTS

## Mandatory Process

1. **Load Context First**
   - Read `.claude/project-manifest.yaml`
   - Read `CLAUDE.md`
   - Load cache via `/load-cache`
   - Read relevant `docs/codebase/` files

2. **Decomposition (Planner Step)**
   - For non-trivial multi-domain work, invoke the `orchestrator` subagent which will produce a Shape A or Shape B plan.
   - Otherwise, break into small independent steps inline.

3. **Execution Rules**
   - Execute ONE step at a time for single-lane work.
   - Dispatch independent lanes in parallel for multi-lane work (concurrent Task tool calls).
   - Delegate to the most appropriate specialist subagent from `.claude/agents/`.
   - Always reference existing patterns.

4. **Anti-Drift Gates (After Every Step)**
   - Self-review against original requirement
   - Run relevant guards (security checklist, schema check, tests)
   - Flag impact on permissions/audits/consents

5. **Final Output**
   - Summary of changes
   - Updated TODO / IMPLEMENTATION_SUMMARY if needed
   - Suggested next step or PR title
