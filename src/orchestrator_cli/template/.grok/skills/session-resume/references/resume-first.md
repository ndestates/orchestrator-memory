# Resume-first mode (token savings)

When `python3 scripts/session-resume-brief.py check --json` returns `"resume_first": "yes"`,
the resume card in `reports/sessions/resume-*.md` is **authoritative** for this session.
Do not re-load the same facts from larger files.

## Which chain?

| Card `Source` | Same calendar day? | Command |
|---------------|--------------------|---------|
| `session-end` | yes | **`/chain session-resume`** |
| `session-end` | no (next day) | `/chain session-start` |
| `eod-shutdown` | any | `/chain session-start` |
| missing/stale | — | `/chain session-start` |

Check JSON fields: `card_source`, `same_day`, `recommended_chain`.

## Gate

**session-start:** fetch → remote_last switch/pull → THEN check/card.

**session-resume:** fetch → checkout session-end card **Branch** (prior session) → THEN check/card. Do not apply remote_last.

```bash
# session-start
python3 scripts/session-context-envelope.py --write
python3 scripts/session-resume-brief.py check --json

# session-resume
python3 scripts/session-resume-land.py
python3 scripts/session-context-envelope.py --write --resume-session
python3 scripts/session-resume-brief.py check --for session-resume --json
```

| Field | Meaning |
|-------|---------|
| `resume_first` | `yes` = lean path; requires fresh card **and** Branch matches checkout |
| `recommended_chain` | `session-resume` or `session-start` |
| `card_source` | From card `Source:` line |
| `same_day` | `yes` if card date is today |
| `card` | Compact handoff — **always print when present** (even if stale) |
| `card_branch_match` | `yes` only when card Branch == current branch after remote_last apply |
| `max_cache_files` | `0` normally; `1` only when card cache caveat mentions stale/rebuild |
| `startup_order` | session-start: `fetch → remote_last → card`. session-resume: `fetch → prior session Branch → card` |
| `continue_target` | session-resume: card Branch. session-start: remote_last |

Freshness: card date is today **or** file age ≤ `token_policy.resume_first_max_hours` (default 24).

**Write policy:** session-end and eod-shutdown must call `session-resume-brief.py write --rich`
with the correct `--source`. Card embeds next-open command (**session-resume** vs **session-start**).

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
Do not use session-resume for stale/eod cards.

## User paste

If the user pastes a resume card block (any model), treat it like `resume_first=yes` for
branch/done/open/cache — still run `check` or `resume-branch.sh` for live sync before edits.

## All platforms

Same script and rules in Grok, Copilot, Claude Code, Cursor, Gemini — paths under
`.grok/`, `.github/`, `.claude/`, `.copilot/` skills; manifests synced from
`.github/project-manifest.yaml`.