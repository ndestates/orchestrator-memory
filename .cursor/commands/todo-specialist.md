# /todo-specialist

> Maintain project TODO-*.md (carry forward, prioritize, update from work). Use on /todo-specialist-agent or when syncing tasks.

**Platform:** Cursor · same skill as Grok `/todo-specialist` · Claude `/todo-specialist`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `What to mark done, add, or reprioritize. e.g. 'mark valuations layout done, add next CDD`

# TODO Specialist Agent

1. Run `/load-project-cache-first`.
2. Read and embody the full instructions in [`.grok/agents/todo-specialist-agent.md`](../../.grok/agents/todo-specialist-agent.md).
3. Output Proposed TODO Updates per canonical format (include branch/date).
4. Per copilot-instructions: ensure today's TODO and tomorrow's on shutdown.
5. Propose only; approval before commit.

Handoffs: structured for main/orchestrator.

User focus (optional): use any extra chat text as $ARGUMENTS.
