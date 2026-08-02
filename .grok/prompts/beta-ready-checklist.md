---
tools: ['search/codebase', 'execute/runInTerminal']
description: "Run a generic beta-readiness pass/fail checklist for any repository."
name: "Beta Ready Checklist"
argument-hint: "Optional scope, e.g. 'api only', 'full stack', 'docs + ci'"
agent: agent

---

# Beta Ready Checklist

Use this prompt to determine whether a repository is ready to move from development to beta.

## Step 1: Load Lean Context
Read only:
1. `.github/project-manifest.yaml`
2. `docs/codebase/README.md`
3. `docs/codebase/CONCERNS.md`
4. Latest file in `TODO/`

Do not run broad source scans unless required by a failed gate.

## Step 2: Evaluate Gates (Pass or Fail)
Assess each gate and produce a one-line reason.

1. Scope Gate: TODO has explicit in-scope beta objectives.
2. Build/Test Gate: There is a runnable, documented validation path for the chosen stack.
3. Security Gate: A documented security review path exists for dependency and input risk.
4. CI Gate: Repository has baseline automation or a tracked plan to add it before beta.
5. Docs Gate: Setup and usage docs are sufficient for a new contributor.
6. Risk Gate: Open concerns/blockers are acknowledged with owners or next actions.

## Step 3: Emit Decision
Output exactly:

- Overall: `PASS` or `FAIL`
- Failed gates: numbered list
- Required actions before beta: numbered list
- Evidence used: list the cache/TODO files read

## Rules
- Keep output under 180 tokens.
- If any gate fails, overall result is `FAIL`.
- Do not claim runtime-specific checks unless they are present in manifest/docs.