---
name: cache-freshness-check
description: "Check docs/codebase cache freshness against manifest cache_stale_days, .codebase-scan.txt, README [UPDATED] markers, git branch, and TODO branch."
argument-hint: "Optional: --json for machine-readable report"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Cache Freshness Check

**Purpose:** Structured check of whether `docs/codebase/` knowledge cache is still trustworthy — not just loaded, but **fresh enough** for the current branch and work.

**Copilot-compatible self-contained.** Run from project root. No reads from `.claude/` or `.github/` required for execution (manifest fallback order is embedded below).

## When to invoke

- Session start (after or instead of guessing staleness in standup)
- Before ``.github/prompts/orchestrator-v2.prompt.md`` medium/high-risk steps
- When `.github/prompts/load-project-cache-first.prompt.md` or `.github/skills/loop-triage/SKILL.md` flags possible staleness
- Weekly loop: `.github/skills/chain/SKILL.md cache-freshness-watch` (patterns/cache-freshness-watch.md)
- User asks: "is the cache stale?", "refresh cache?", "cache out of date?"
- After branch switch, merge, or major feature landing on `develop`/`master`

## Phase 0 — Manifest (required)

Read **one** manifest (first found, prefer platform):

1. `.grok/project-manifest.yaml` (Grok)
2. `.claude/project-manifest.yaml` (Claude)
3. `.github/project-manifest.yaml` (Copilot canonical / default here)

Extract `token_policy.cache_stale_days` (default **14** if missing). See `docs/reference/manifest.md`.

## Phase 1 — Run checker script (required)

```bash
python3 .github/skills/cache-freshness-check/scripts/cache_freshness_check.py
```

For handoffs / chaining:

```bash
python3 .github/skills/cache-freshness-check/scripts/cache_freshness_check.py --json
```

**Do not** read application source. The script uses only:

- `docs/codebase/.codebase-freshness.txt` (preferred) or `.codebase-scan.txt` — `Generated:` dates (script reads locally; agent must not Read full scan)
- `docs/codebase/README.md` — `[UPDATED]` / `[CACHED]` headers
- Latest `TODO/*_TODO.md` — `**Branch:**` and `**Resume branch (remote-last):**` lines
- `bash scripts/resume-branch.sh` — live remote-last (session-start primary)
- `git branch --show-current`

## Phase 2 — Classify (script output)

| Status | Rule |
|--------|------|
| **fresh** | Age ≤ half of `cache_stale_days` (min 3 days) |
| **aging** | Age > half threshold but ≤ `cache_stale_days` |
| **stale** | Age > `cache_stale_days` OR no parseable cache dates |
| **branch_drift** | `current_branch` ≠ TODO branch and/or ≠ branch named in `.codebase-scan.txt` |

**Combined verdict:** report `status` + `branch_drift` separately. Example: `aging + branch_drift`.

## Phase 3 — Advise (required)

Map to recommendations (script prints these; agent may add context from CONCERNS only if already loaded):

| Condition | Recommend |
|-----------|-----------|
| **stale** | `.github/prompts/read-codebase.prompt.md` or `.github/skills/chain/SKILL.md cache-rebuild` |
| **aging** | Targeted `.github/prompts/read-codebase.prompt.md` delta on current branch |
| **branch_drift** | `.github/skills/chain/SKILL.md cache-rebuild` or targeted scan + `/branch-context-agent` |
| **fresh**, no drift | Continue with `.github/prompts/load-project-cache-first.prompt.md` — no full rescan |

**Never auto-run** `.github/prompts/read-codebase.prompt.md` without user approval unless they explicitly asked to refresh.

## Phase 4 — Response format (required)

```markdown
## Cache freshness

- **Status:** fresh | aging | stale (+ branch_drift if true)
- **Last activity:** YYYY-MM-DD (N days ago; policy: 14d)
- **Branch:** `<current>` | TODO: `<todo>` | scan: `<scan>`
- **Cache cited:** docs/codebase/.codebase-scan.txt, docs/codebase/README.md, TODO/…

**Recommend:** <1–3 bullets from script>

**Next Steps**
1. …
```

### Handoff JSON (≤80 tokens for chains)

```json
{"cache_stale":false,"status":"fresh","branch_drift":false,"age_days":2,"recommend":".github/prompts/load-project-cache-first.prompt.md"}
```

Use `cache_stale: true` when `status` is `stale` OR (`aging` + `branch_drift`).

## Integration

| Skill / chain | Role |
|---------------|------|
| `.github/prompts/load-project-cache-first.prompt.md` | May delegate structured check here instead of ad-hoc guess |
| `.github/skills/loop-triage/SKILL.md` | Optional staleness section via this skill |
| `.github/skills/documentation-specialist/SKILL.md` | Use `cache_stale` handoff from this check |
| ``.github/prompts/orchestrator-v2.prompt.md`` | Run before medium/high-risk if cache not checked this session |
| `.github/skills/chain/SKILL.md cache-rebuild` | Fix path when stale |
| `.github/skills/chain/SKILL.md documentation-full` | Stale cache + full doc site |

## Anti-patterns

- Full-file reads of all `docs/codebase/*.md` (use script + grep)
- Treating xAI prompt cache (`/token-usage-meter`) as docs cache
- Auto-running `.github/prompts/read-codebase.prompt.md` on `aging` without user direction
- Skipping branch_drift when TODO and git disagree

## Related

- `.github/skills.github/prompts/load-project-cache-first.prompt.md/SKILL.md`
- `.github/skills.github/prompts/read-codebase.prompt.md/SKILL.md`
- `.copilot/memories/INDEX.md` — `cache_stale_days` rule
- `chains/registry.yaml` — `cache-rebuild`, `documentation-full`