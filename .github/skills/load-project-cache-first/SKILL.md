---
name: load-project-cache-first
description: "Load project project cache (docs/codebase/ + TODO + CONCERNS + .grok/.copilot memories) first before any deep exploration."
argument-hint: "Optional: specific cache file or topic, e.g. 'CONCERNS', 'Filament panels', 'architecture', 'valuations'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Load Local Codebase Cache First (Token-Efficient Session Start)

**This is the MASTER LOADER skill for the project project.**

**MANDATORY FIRST STEP for most tasks on this project.**

Before performing any semantic_search, grep, or reading large numbers of source files, you **must** load the local knowledge cache.

**Read *your* platform manifest first** — honor `token_policy.max_cache_files_default`, `grep_before_read`, and `no_source_until_confirmed`.

| Host | Manifest (primary only) |
|------|-------------------------|
| **Grok (this skill)** | **`.grok/project-manifest.yaml`** · skills under **`.github/skills/`** |
| Claude | `.claude/project-manifest.yaml` |
| Copilot | `.github/project-manifest.yaml` |
| Gemini | `.gemini/project-manifest.yaml` |
| Cursor | `.cursor/project-manifest.yaml` |

Do **not** load another host’s skill tree as primary. Shared OK: `TODO/`, `docs/codebase/`, `scripts/`. See `docs/reference/platform-surfaces.md`.

**Manifest identity gate (mandatory — any model):** after opening the manifest (or MCP `get_project_manifest`), run:

```bash
python3 scripts/check-project-manifest.py --json
```

If `status` is `template_residue` or `warn`, cite `briefing_line` + issues — the file may still be the orchestrator **Project Template** defaults, not this app. Do not assume stack/runtime from residue. Orchestrator source repo is allowed to keep template values (`ok`).

## Spine (always — does not count toward cap)

1. `docs/codebase/README.md` (index — section read or first 80 lines)
2. `docs/codebase/.codebase-freshness.txt` (lean freshness + stack summary, ≤35 lines)
3. Latest `TODO/*.md` (branch header + open bullets via grep)
4. `.copilot/memories/INDEX.md` (tier-1 table)
5. `.copilot/memories/who-i-am.md` if present (operator profile — first 40 lines or grep `**Primary Goals:**` section; free spine)

**Loop-enabled apps** (`LOOP.md` exists — does not count toward cap):

6. `STATE.md` — grep `## Lessons → skills`, `## Stale flags`, `## Compound queue` (section read only)
7. `VISION.md` — standing spec (first section or ≤40 lines)

Loaded before or with `/app-compound-gate` during `.github/skills/chain/SKILL.md session-start`. Treat STATE lessons as authoritative over chat memory.

**Never Read `docs/codebase/.codebase-scan.txt` here** — it is the full scan artifact (500+ lines). Full scan is `.github/skills/acquire-codebase-knowledge/SKILL.md` only. If `.codebase-freshness.txt` is missing, run `cache_freshness_check.py --json`; do not Read the scan file.

**MCP-first:** Prefer `get_project_manifest`, `read_cache_file`, `get_latest_todo` (bounded slices). Use `docs/codebase/SECTIONS.md` to pick sections before any full-file Read.

## Additional cache (cap: `max_cache_files_default`, default **2**)

Pick only what the task needs from `docs/codebase/`:
   - Architecture / overall understanding → `docs/codebase/ARCHITECTURE.md`
   - Tech stack and versions → `docs/codebase/STACK.md`
   - Directory layout and panels → `docs/codebase/STRUCTURE.md`
   - Rules, conventions, DDEV, DB safety → `docs/codebase/CONVENTIONS.md`
   - External integrations → `docs/codebase/INTEGRATIONS.md`
   - Testing rules and CI → `docs/codebase/TESTING.md`
   - Known risks and open items → `docs/codebase/CONCERNS.md` (recommended first pick)
5. At most **one** INDEX-selected memory file (counts toward cap if you already loaded 2 codebase docs).

**Grep-before-read (mandatory when `grep_before_read: true`)**:
- For any cache file >80 lines: `Grep` headings or keywords first; then `Read` with `offset`/`limit` for one section only.
- Do **not** read `chains/registry.yaml`, full skills, or app source until the user confirms direction — unless the task names an exact path.

**Rules for token efficiency**:
- Treat the cache files as your primary source of truth.
- Only read application source **after** cache load **and** user direction is clear (`no_source_until_confirmed`).
- If the cache appears stale, run `/cache-freshness-check` for a structured report, then ask the user before doing a full re-scan.
- When answering, cite the specific cache file(s) you used.

After loading the cache, confirm to the user with the list of loaded files.

Follow `.github/copilot-instructions.md` (DDEV, security, data safety) at all times.

See also the full prompt definition in `.github/prompts.github/prompts/load-project-cache-first.prompt.md.md`.
