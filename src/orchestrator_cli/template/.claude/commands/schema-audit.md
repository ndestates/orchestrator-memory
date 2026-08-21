---
description: Read-only schema/migration auditor for project. Use on /schema-audit or for drift analysis.
argument-hint: Scope or tables, e.g. 'valuations', 'Property* models', 'recent migrations'
allowed-tools: Read, Grep, Glob, Bash
---

# Schema Audit Agent

1. Run `/load-cache` (CONVENTIONS, TESTING, CONCERNS, model checker config).
2. Read and embody the full instructions in [`.claude/agents/schema-audit.md`](../../.claude/agents/schema-audit.md).
3. Read-only + safe DDEV inspection on test DB.
4. Structured output with mismatches, migration refs, risks.
5. No execution of changes.

Cite caches. Follow data safety.

User focus (optional): $ARGUMENTS
