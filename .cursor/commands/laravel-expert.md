# /laravel-expert

> Laravel 12 + Filament 5 expert for project. Use for architecture, resources, Eloquent, panels, services, Artisan, testing, or when /laravel-expert-agent.

**Platform:** Cursor · same skill as Grok `/laravel-expert` · Claude `/laravel-expert`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Task description, e.g. 'add valuation resource to Sales panel', 'fix observer for Property`

# Laravel Expert Agent

1. Run `/load-project-cache-first` (STRUCTURE for panels, ARCHITECTURE, CONVENTIONS).
2. Read and embody the full instructions in [`.grok/agents/laravel-expert-agent.md`](../../.grok/agents/laravel-expert-agent.md).
3. Strictly use DDEV for all commands (see ddev-local-runtime skill).
4. Run security checklist after relevant changes.
5. Follow data safety, no destructive on live db.
6. Update TODO via specialist if major; leave clean state.

Cite cache files used.

User focus (optional): use any extra chat text as $ARGUMENTS.
