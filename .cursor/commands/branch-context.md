# /branch-context

> Branch scope and TODO-alignment analyzer for project. Summarize branch purpose, changes vs active TODO, detect drift before merge or major work. Use when user runs /branch-context-agent or orchestr...

**Platform:** Cursor · same skill as Grok `/branch-context` · Claude `/branch-context`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Provide branch name and what context you need summarized.`

# Branch Context Agent

1. Run `/load-project-cache-first`.
2. Read and embody the full instructions in [`.grok/agents/branch-context-agent.md`](../../.grok/agents/branch-context-agent.md).
3. Gather branch info (`git branch --show-current`, log, status), cross vs TODO.
4. Report alignment verdict (aligned/partial/misaligned) + risks + next actions.
5. Cite caches used.

Handoffs: include branch_context details for main agent.

User focus (optional): use any extra chat text as $ARGUMENTS.
