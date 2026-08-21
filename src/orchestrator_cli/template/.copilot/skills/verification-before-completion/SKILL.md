---
name: verification-before-completion
description: "Evidence before any done/fixed/passing claim. Run the proof command fresh, read output, then claim. Use before commit, PR, or handoff."
argument-hint: "Claim to prove, e.g. 'tests pass', 'bug fixed', 'build ok'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Verification Before Completion

**Purpose:** Do not claim done, fixed, passing, or complete without **fresh command output** in this turn.

**Adapted from:** obra/superpowers `verification-before-completion` (MIT). Orchestrator additions: test-safety, manifest test command.

**Iron law:** no completion claims without fresh verification evidence.

## Complements (do not duplicate)

| Skill | Role |
|-------|------|
| test-safety-agent | Confirm test DB / non-destructive *before* you run tests |
| test-specialist-agent | Author the test that becomes the proof |
| qa-agent | Broader readiness sign-off |
| systematic-debugging | When the proof fails |

## Gate (every claim)

1. **Identify** the command that proves the claim (`runtime.test_command` from the manifest, or the exact repro).
2. **Safety** — `/test-safety-agent` if the command hits a database. Never live DB.
3. **Run** the full command now. Not a previous turn. Not "should pass".
4. **Read** exit code and failure count.
5. **Then** state the claim **with** that evidence — or state the actual failure.

Skip a step = you did not verify.

## What counts

| Claim | Proof |
|-------|--------|
| Tests pass | Test command: 0 failures |
| Bug fixed | Original symptom command now passes |
| Build succeeds | Build command: exit 0 |
| Lint clean | Linter: 0 errors (lint ≠ compile) |
| Agent finished | `git diff` / files on disk match the claim |
| Requirements met | Checklist against the plan, item by item |

Not sufficient: prior run, "looks correct", agent self-report, linter as a stand-in for tests.

## Red flags

- "should", "probably", "seems to", "Great!", "Done!" before a run
- About to commit / PR / mark TODO done without output
- Partial suite used to imply the full suite
- Tired and wanting the work over

## Output

```markdown
verify: claim=<text>; cmd=<exact>; exit=<n>; result=pass|fail
evidence: <one line from output>
```

If fail → `/systematic-debugging` or report the real status. Do not rephrase failure as success.

## Related

- Source: https://github.com/obra/superpowers
- Ports: `reports/research/ports/skills-sh/README.md`
