# /test-safety

> Enforce test DB safety and pre/post risk assessment for project tests. Use before running tests or on /test-safety-agent.

**Platform:** Cursor · same skill as Grok `/test-safety` · Claude `/test-safety`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Test scope or change description`

# Test Safety Agent

1. Run `/load-project-cache-first` (TESTING.md, CONVENTIONS, CONCERNS).
2. Read and embody the full instructions in [`.grok/agents/test-safety-agent.md`](../../.grok/agents/test-safety-agent.md).
3. Confirm DB_DATABASE=test or :memory: via ddev.
4. Snapshot counts if needed; never destructive on live db.
5. All tests via DDEV.
6. Report safety + cache citation.

Halt on violations. See copilot-instructions §5-6.

User focus (optional): use any extra chat text as $ARGUMENTS.
