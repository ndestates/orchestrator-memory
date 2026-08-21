# Model Schema Check (Cache-First + Safe)

**First action**: Load cache via `load-project-cache-first.md`.

## Required Cache Reads
- `docs/codebase/CONVENTIONS.md` — Migration and schema rules (never blanket migrate, use --path, safety checks)
- `docs/codebase/TESTING.md` — Test DB rules (always target `test`)
- `docs/codebase/CONCERNS.md` — Any open schema-related items
- `config.github/prompts/model-schema-check.prompt.mder.php` — Project-specific checker configuration (if present)
- `.copilot/memories/INDEX.md`

## Execution Rules (non-negotiable)
- All checks must run against the `test` database only.
- Never run destructive commands on `db`.
- Use the project's checker script/config where available.
- Prefer read-only inspection (`php artisan model-schema-check` or equivalent if defined).
- All commands via DDEV (`ddev exec ...`).

## Output Requirements
- List of models/tables checked
- Any mismatches found (columns, types, indexes, foreign keys)
- Mapping to specific migration files
- Reference to numbered CONCERNS items if applicable
- Safe remediation suggestions only (no auto-execution)

Always cite the exact cache files and lines used.

Follow `.github/copilot-instructions.md` §5-7 for data safety.
