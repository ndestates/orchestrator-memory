---
description: Laravel 12 + Filament 5 expert for project. Use for architecture, resources, Eloquent, panels, services, Artisan, testing, or when /laravel-expert.
argument-hint: Task description, e.g. 'add valuation resource to Sales panel', 'fix observer for Property'
allowed-tools: Read, Grep, Glob, Bash
---

# Laravel Expert Agent

1. Run `/load-cache` (STRUCTURE for panels, ARCHITECTURE, CONVENTIONS).
2. Read and embody the full instructions in [`.claude/agents/laravel-expert.md`](../../.claude/agents/laravel-expert.md).
3. Strictly use DDEV for all commands (see ddev-local-runtime skill).
4. Run security checklist after relevant changes.
5. Follow data safety, no destructive on live db.
6. Update TODO via specialist if major; leave clean state.

Cite cache files used.

User focus (optional): $ARGUMENTS
