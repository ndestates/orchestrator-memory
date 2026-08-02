# Resume-first mode (token savings)

When `python3 scripts/session-resume-brief.py check --json` returns `"resume_first": "yes"`,
the resume card in `reports/sessions/resume-*.md` is **authoritative** for this session.
Do not re-load the same facts from larger files.

## Gate (always on session-start)

```bash
# Preferred entry — ORDER: fetch → remote_last switch/pull → THEN check/card
python3 scripts/session-context-envelope.py --write
# Explicit check (after switch; card from post-switch tree):
python3 scripts/session-resume-brief.py check --json
```

| Field | Meaning |
|-------|---------|
| `resume_first` | `yes` = lean path; requires fresh card **and** Branch matches checkout |
| `card` | Compact handoff — **always print when present** (even if stale) |
| `card_branch_match` | `yes` only when card Branch == current branch after remote_last apply |
| `card_present` / `surface_card` | `yes`/`always` when a resume-*.md exists |
| `max_cache_files` | `0` normally; `1` only when card cache caveat mentions stale/rebuild |
| `skip` | Do not Read these sources for branch/done/open/WIP |
| `defer` | Skip unless user asks or task requires |
| `keep` | Still run (scripts, not large context) |
| `startup_order` | `fetch → remote_last switch/pull → then card` |

Freshness: card date is today **or** file age ≤ `token_policy.resume_first_max_hours` (default 24).

**Write policy:** session-end and eod-shutdown must call `session-resume-brief.py write --rich`
and print the **next session-start remote_last-first** order reminder (embedded in the card).

## When `resume_first=yes` — SKIP (hard)

| Skip id | Agent rule |
|---------|------------|
| `todo_full_read` | Open items are on the card — no full `TODO/*.md` Read |
| `state_read` | No `STATE.md` Read (lessons/facts) unless user asks |
| `vision_read` | No `VISION.md` Read |
| `vault_todo_open_resynthesis` | No `session-vault-todo-query` re-listing open work already on card |
| `git_status_narrative` | Trust card branch + dirty line — no `git status` prose |
| `compound_gate_lessons_dump` | Skip compound-gate lesson dump; offer only on user ask |

## When `resume_first=yes` — DEFER (optional steps)

- `wiki_brief` — skip unless wiki task
- `changelog_init` — skip unless unreleased work
- `extra_codebase_docs` — no ARCHITECTURE/CONCERNS unless cache caveat requires one file

## When `resume_first=yes` — KEEP (lightweight)

**Preferred (all platforms):**

```bash
python3 scripts/session-context-envelope.py --write
```

Print compact CTX only (see `docs/reference/session-context-token-budget.md`). Covers identity, MCP dev-only, branch/sync, vault, sec pointer, open/next.

**Fallback** if envelope script missing on older deploys:

- `bash scripts/detect-project-runtime.sh --with-manifest-identity`
- `python3 scripts/check-project-manifest.py --json`
- `git fetch` + `bash scripts/resume-branch.sh --apply` (auto-switch remote_last when clean)
- `bash scripts/session-security-sweep.sh`
- Vault: `session-vault-brief.py --json` (≤2 events)

When MCP is not ready: expand `mcp_start` options only if needed. Never offer MCP on public/production hosts.

## When `resume_first=no`

Run full `/chain session-start` (TODO, STATE, vault, cache spine per `cache-efficient`).

## User paste

If the user pastes a resume card block (any model), treat it like `resume_first=yes` for
branch/done/open/cache — still run `check` or `resume-branch.sh` for live sync before edits.

## All platforms

Same script and rules in Grok, Copilot, Claude Code, Cursor, Gemini — paths under
`.grok/`, `.github/`, `.claude/`, `.copilot/` skills; manifests synced from
`.github/project-manifest.yaml`.