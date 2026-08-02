# /schema-audit

> Read-only schema/migration auditor for project. Use on /schema-audit-agent or for drift analysis.

**Platform:** Cursor · same skill as Grok `/schema-audit` · Claude `/schema-audit`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Scope or tables, e.g. 'valuations', 'Property* models', 'recent migrations`

# Schema Audit Agent

1. Run `/load-project-cache-first` (CONVENTIONS, TESTING, CONCERNS, model checker config).
2. Read and embody the full instructions in [`.grok/agents/schema-audit-agent.md`](../../.grok/agents/schema-audit-agent.md).
3. Read-only + safe DDEV inspection on test DB.
4. Structured output with mismatches, migration refs, risks.
5. No execution of changes.

Cite caches. Follow data safety.

User focus (optional): use any extra chat text as $ARGUMENTS.
