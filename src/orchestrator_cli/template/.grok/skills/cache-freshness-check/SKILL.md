---
name: cache-freshness-check
description: "Check docs/codebase cache freshness against manifest cache_stale_days, .codebase-scan.txt, README [UPDATED] markers, git branch, and TODO branch."
argument-hint: "Optional: --json for machine-readable report"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
verified_at: "2026-08-16"
self_regulating: true
covers:
  - .grok/skills/cache-freshness-check
  - docs/codebase
  - TODO
  - scripts/skill_health.py
---
# Cache Freshness Check

**Purpose:** Structured check of whether `docs/codebase/` knowledge cache is still trustworthy — not just loaded, but **fresh enough** for the current branch and work.

**Grok-native self-contained.** Run from project root. No reads from `.claude/` or `.github/` required for execution (manifest fallback order is embedded below).

## When to invoke

- Session start (after or instead of guessing staleness in standup)
- Before `/orchestrator` medium/high-risk steps
- When `/load-project-cache-first` or `/loop-triage` flags possible staleness
- Weekly loop: `/chain cache-freshness-watch` (patterns/cache-freshness-watch.md)
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
python3 .grok/skills/cache-freshness-check/scripts/cache_freshness_check.py
```

For handoffs / chaining:

```bash
python3 .grok/skills/cache-freshness-check/scripts/cache_freshness_check.py --json
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
| **stale** | `/read-codebase` or `/chain cache-rebuild` |
| **aging** | Targeted `/read-codebase` delta on current branch |
| **branch_drift** | `/chain cache-rebuild` or targeted scan + `/branch-context-agent` |
| **fresh**, no drift | Continue with `/load-project-cache-first` — no full rescan |

**Never auto-run** `/read-codebase` without user approval unless they explicitly asked to refresh.

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
{"cache_stale":false,"status":"fresh","branch_drift":false,"age_days":2,"recommend":"/load-project-cache-first"}
```

Use `cache_stale: true` when `status` is `stale` OR (`aging` + `branch_drift`).

## Integration

| Skill / chain | Role |
|---------------|------|
| `/load-project-cache-first` | May delegate structured check here instead of ad-hoc guess |
| `/loop-triage` | Optional staleness section via this skill |
| `/documentation-specialist` | Use `cache_stale` handoff from this check |
| `/orchestrator` | Run before medium/high-risk if cache not checked this session |
| `/chain cache-rebuild` | Fix path when stale |
| `/chain documentation-full` | Stale cache + full doc site |

## Anti-patterns

- Full-file reads of all `docs/codebase/*.md` (use script + grep)
- Treating xAI prompt cache (`/token-usage-meter`) as docs cache
- Auto-running `/read-codebase` on `aging` without user direction
- Skipping branch_drift when TODO and git disagree

The checker also reports `skill_stale` from `scripts/skill_health.py scan` (advisory).

## Self-regulation (mandatory)

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**This skill's checks:**
- Ran the checker script (did not guess freshness)
- Did not auto-run `/read-codebase`

Then: `python3 scripts/skill_health.py log --skill cache-freshness-check --score 0.0-1.0 --notes "fresh|aging|stale"`

## Related

- `.grok/skills/load-project-cache-first/SKILL.md`
- `.grok/skills/read-codebase/SKILL.md`
- `.grok/memories/INDEX.md` — `cache_stale_days` rule
- `chains/registry.yaml` — `cache-rebuild`, `documentation-full`