---
description: Enforce test DB safety and pre/post risk assessment for project tests. Use before running tests or on /test-safety.
argument-hint: Test scope or change description
allowed-tools: Read, Grep, Glob, Bash
---

# Test Safety Agent

1. Run `/load-cache` (TESTING.md, CONVENTIONS, CONCERNS).
2. Read and embody the full instructions in [`.claude/agents/test-safety.md`](../../.claude/agents/test-safety.md).
3. Confirm DB_DATABASE=test or :memory: via ddev.
4. Snapshot counts if needed; never destructive on live db.
5. All tests via DDEV.
6. Report safety + cache citation.

Halt on violations. See copilot-instructions §5-6.

User focus (optional): $ARGUMENTS
