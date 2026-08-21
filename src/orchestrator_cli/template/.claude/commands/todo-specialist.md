---
description: Maintain project TODO-*.md (carry forward, prioritize, update from work). Use on /todo-specialist or when syncing tasks.
argument-hint: What to mark done, add, or reprioritize. e.g. 'mark valuations layout done, add next CDD'
allowed-tools: Read, Grep, Glob, Bash
---

# TODO Specialist Agent

1. Run `/load-cache`.
2. Read and embody the full instructions in [`.claude/agents/todo-specialist.md`](../../.claude/agents/todo-specialist.md).
3. Output Proposed TODO Updates per canonical format (include branch/date).
4. Per copilot-instructions: ensure today's TODO and tomorrow's on shutdown.
5. Propose only; approval before commit.

Handoffs: structured for main/orchestrator.

User focus (optional): $ARGUMENTS
