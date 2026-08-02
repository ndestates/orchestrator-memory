# .grok/memories/ for project

Cross-session and repo memory for Grok. Symlinked to `.copilot/memories/` (the canonical shared with Copilot instructions / other tools).

## Structure
- `INDEX.md` — Read this first. Tiered guidance: always-load + topic pick ≤3.
- `repo/` (symlink → `.copilot/memories/repo/`) — Long-lived repo facts, caches from /read-codebase, feature summaries (e.g. valuations, CDD).
- `session/` (symlink → `.copilot/memories/session/`) — Per-session notes that survived compaction or were /flush'ed.
- Some high-value memories may be hard-linked or copied at .grok/memories/ root for quick access.

## Usage
Per load-project-cache-first and daily-standup-with-cache: read INDEX + docs/codebase/ sections + key 1-3 memories before source dives.

See `.grok/README.md` and user-guide/13-memory.md .

Caches implemented as part of this setup (symlinks + INDEX).
