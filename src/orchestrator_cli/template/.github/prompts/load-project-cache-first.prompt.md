# Load Local Codebase Cache First (Token-Efficient Session Start)

**This is the MASTER LOADER prompt for the project project.**

**MANDATORY FIRST STEP for most tasks on this project.**

**Session-start token gate** — run before cache load:

```bash
python3 scripts/session-resume-brief.py check --json
```

When `resume_first=yes`: print `card` only; `max_cache_files=0` (or 1 if cache caveat on
card); skip TODO/STATE/VISION reads. See `.github/skills/session-resume/references/resume-first.md`.

Read your platform manifest first (`.grok/project-manifest.yaml` for Grok Build; `.claude/project-manifest.yaml` for Claude Code; see `docs/reference/manifest.md` for table) — honor `max_cache_files_default` (default 2), `grep_before_read`, `no_source_until_confirmed`.

**Spine (does not count toward cap):** README index, `.codebase-freshness.txt` (≤35 lines — **never** `.codebase-scan.txt`), latest TODO, `INDEX.md`.

Before source reads, load at most **`max_cache_files_default`** additional `docs/codebase/*` files:

1. Read `docs/codebase/README.md` (the index).
2. Pick the most relevant files (≤2 total from cache):
   - Architecture / overall understanding → `docs/codebase/ARCHITECTURE.md`
   - Tech stack and versions → `docs/codebase/STACK.md`
   - Directory layout and panels → `docs/codebase/STRUCTURE.md`
   - Rules, conventions, DDEV, DB safety → `docs/codebase/CONVENTIONS.md`
   - External integrations → `docs/codebase/INTEGRATIONS.md`
   - Testing rules and CI → `docs/codebase/TESTING.md`
   - Known risks and open items → `docs/codebase/CONCERNS.md` (always recommended)
3. Grep headings before full reads; use section `Read` only.
4. Do not read app source or full `chains/registry.yaml` until user confirms direction.

**Rules for token efficiency**:
- Treat the cache files as your primary source of truth.
- Only read source code after cache load and user direction is clear.
- If the cache appears stale (no [UPDATED] marker in the last 7–14 days, or major changes have occurred), note this and ask the user before doing a full re-scan.
- When answering, cite the specific cache file(s) you used (e.g., "Per CONCERNS.md item 5.1...").

**When to skip this prompt**:
- Only during the initial full `read-codebase` execution (see `read-codebase.prompt.md`).
- When the user explicitly says "ignore cache and do fresh scan".

After loading the cache, confirm to the user:
> "Local codebase cache loaded from docs/codebase/ + .copilot/memories/. Proceeding with task using cached knowledge + targeted file reads where needed."

---

## Related Cache-Aware Prompts in This Directory

Use these after (or instead of) the master loader when the task is focused:

- `daily-standup-with-cache.md` — Recommended default for most normal development/review sessions (combines TODO + CONCERNS + cache).
- `filament-panel-review.md` — For any work on the Filament panels (Admin, Documents, Signature Requests, Users).
- `model-schema-check.md` — Before/after migrations or when schema drift is suspected.
- `read-codebase.md` — Only for the rare full re-scan + cache refresh.

This prompt + the files above form the official token-saving prompt library for project.

Follow `.github/copilot-instructions.md` (DDEV mandatory, DB safety, security checklist, etc.) at all times.
