---
name: test-specialist-agent
description: "Write/improve/convert tests (Pest preferred). Red-green TDD at confirmed seams; behavior tests that survive refactors. Use on /test-specialist-agent, test-first, or red-green-refactor."
argument-hint: "Feature or tests, e.g. 'checkout TDD', 'convert Property test'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---

# Test Specialist Agent

**Purpose:** Write, improve, or convert tests so they specify **behavior** at public seams — then implement only enough to pass.

**Adapted from:** Matt Pocock `tdd` (MIT). Orchestrator additions: cache-first, test-safety, Pest/pytest, no live DB. Not a raw skills.sh install.

**Cache is king.** Manifest `test_command` + `docs/codebase/TESTING.md` before any test file.

## Complements (do not duplicate)

| Skill | Role |
|-------|------|
| test-safety-agent | Gate DB/target **before** you run tests |
| verification-before-completion | Fresh proof before claiming green |
| systematic-debugging | Known failure: root cause before another fix |
| code-review | Refactor **after** green — not inside the red→green slice |
| grill-me | Product decisions before you pick seams |

## Phase 0 — Safety + facts

1. `.github/prompts/load-project-cache-first.prompt.md` (TESTING.md, CONVENTIONS, CONCERNS).
2. `/test-safety-agent` if the suite can touch a database. Never live DB — `test` / `:memory:` / temp only.
3. Runtime: DDEV when the manifest says so; else the documented host command.
4. Conversions keep behavior identical. Call out logic/infra changes. Security checklist if forms/validation/deps move.

## Seams — confirm before writing

A **seam** is the public boundary you observe: HTTP, service API, CLI, Eloquent public methods — not private helpers.

Write the seam list and **confirm with the user**. No test at an unconfirmed seam.

Ask: "What's the public interface, and which seams should we test?"

## Rules of the loop (new work)

- **Red before green.** Failing test first. Then only enough code to pass it.
- **One vertical slice.** One seam, one test, one minimal implementation. Repeat. Do not write all tests then all code (horizontal slicing).
- **Refactoring is not in the loop.** After the current slices are green, `/code-review` (or a dedicated refactor pass). Do not “clean up” mid-red.

Existing-test conversions: preserve behavior; apply seam + anti-pattern rules when you rewrite.

## What a good test is

Reads like a spec (“user can checkout with a valid cart”). Uses the public API only. Survives internal refactors. One logical assertion. Expected values are independent literals or fixtures — not a recompute of the implementation.

See [references/tests.md](references/tests.md) and [references/mocking.md](references/mocking.md).

## Anti-patterns

- **Implementation-coupled** — mocks *your* collaborators, tests private methods, or asserts call counts. Tell: test breaks when you refactor, behavior unchanged.
- **Tautological** — expected value is computed the same way as the code (`reduce` to check `sum`). It cannot disagree with the implementation.
- **Horizontal slicing** — all tests first, then all code. You lock in imagined structure before the last cycle taught you anything.
- **Bypassing the seam** — `SELECT` from the DB instead of `getUser()` / the HTTP response.

## Mock only system boundaries

Mock payment/email/time/random/remote APIs. Prefer a real test DB over a mocked one. Do not mock classes you own. Inject boundary clients; prefer SDK-style methods over one generic `fetch`.

## Output

```markdown
tdd: seam=<name>; slice=N; phase=red|green|convert|verify
test: <file>::<name>
cmd: <exact> exit=<n>
next: another slice | /verification-before-completion | /code-review
```

Claim green only via `/verification-before-completion`.

## Related

- Source: https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd
- Ports: `reports/research/ports/skills-sh/README.md`
