---
name: cache-efficient
description: "project cache-first session with minimal tokens: load INDEX + targeted cache/memories only, respond in short bullets."
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---
# Cache-Efficient Mode

**Non-negotiable for this repo**: maximize cached knowledge; minimize tokens.

## Resume-first (session-start — check before load)

```bash
python3 scripts/session-resume-brief.py check --json
```

When `resume_first=yes`: trust the card; **do not** load spine items already on the card
(TODO full read, STATE, VISION). Use `max_cache_files` from check (usually 0). Rules:
`.grok/skills/session-resume/references/resume-first.md`.

## Load (do not skip unless resume_first=yes)

Read manifest `token_policy` first.

**Spine (free, bounded reads only):**

| File | Max read |
|------|----------|
| `docs/codebase/README.md` | First 80 lines OR grep `##` headings then one section |
| `docs/codebase/SECTIONS.md` | Heading index — grep then section Read only |
| `docs/codebase/.codebase-freshness.txt` | **Whole file only** (≤35 lines) — stack + scan date |
| Latest `TODO/*.md` | Open items + branch header only (`Grep` `- [ ]` / `**Branch:**`) |
| `.grok/memories/INDEX.md` | Tier-1 table only (first 25 lines) |

**Freshness — use `.codebase-freshness.txt`, never `.codebase-scan.txt`:**

- `.codebase-scan.txt` is a **full scan artifact** (tree, CI heads, TODO walk, manifests) — often 500+ lines.
- **FORBIDDEN in cache-efficient / session-start / load-cache:** `Read` on `docs/codebase/.codebase-scan.txt`.
- If `.codebase-freshness.txt` is missing, run (do not Read scan yourself):
  ```bash
  python3 .grok/skills/cache-freshness-check/scripts/cache_freshness_check.py --json
  ```
  Or ask user to run `/chain cache-rebuild` — do **not** run `scan.py` or walk the repo.

**Capped loads** (`max_cache_files_default`, default **2**):

1. ≤2 files from `docs/codebase/*` (excluding `.codebase-scan.txt`) — **grep headings first**, then section `Read` only.
2. ≤1 INDEX-selected memory (counts toward cap if 2 codebase docs already loaded).

Optional: `IMPLEMENTATION_SUMMARY.md` / `BRANCH_ANALYSIS.md` — **one section** only if task requires; prefer grep.

## Forbidden in lean mode (hard stop)

Never during cache load or standup unless the user explicitly requests a full scan:

| Action | Why |
|--------|-----|
| `Read docs/codebase/.codebase-scan.txt` | Full scan dump — use `.codebase-freshness.txt` |
| Run `scan.py`, `/read-codebase`, `/acquire-codebase-knowledge` | Walks entire codebase |
| `Glob **/*` or broad `Grep` without path scope | Implicit full-repo scan |
| `Read chains/registry.yaml` in full | Grep chain `id:` / `intents:` only |
| `Read` any skill/prompt >80 lines | Use chain handoff or grep the one section needed |
| `Read` application source trees | Until user confirms direction |

## Respond

- Default cap: **≤120 words** unless user asks for detail, code, or a plan.
- Format: bullets; one line per finding; cite `path` or `path:line` — **no** large code fences.
- Reference cache by name (“per CONCERNS §…”, “per project-cache”) — do not quote paragraphs.
- End with **Next** (1–3 numbered actions) when helpful.
- Orchestrator JSON / handoff schemas: still valid when that skill requires them — keep JSON compact.

## After load, confirm in one line

Example: `Cache: README + .codebase-freshness.txt + CONCERNS(§6) + TODO. Fresh. Ready.`

## Token meter (always-on)

When `token_policy.report_tokens_estimate: true` (manifest default), end **every substantive response** with the one-line footer from `/token-usage-meter`:

1. Run `python3 .grok/skills/token-usage-meter/scripts/token_monitor.py --sync --project .` once per turn.
2. Append the printed line: `Token meter: ctx … · +… this turn · … turns · STATUS`.
3. Surface any WARNINGS above the footer.

**Auto-lean on meter status:**

| Status | Agent behavior |
|--------|----------------|
| OK | Normal cache-efficient |
| WARNING (≥100k ctx or ≥15k turn delta) | ≤120 words; no new cache files; no source; MCP-only reads |
| CRITICAL (≥128k) | Stop expanding context; offer fresh session; handoff bullets only |

Skip footer only for trivial acks or when user opts out (`no token meter`).

## Chaining

- **Auto-compose:** `/chain <intent>` — discovers skills from `chains/registry.yaml`, one shared cache load, minimal handoffs (see `CHAIN.md`).
- Standup: `/chain session-start` or `/daily-standup-with-cache` then stay in cache-efficient tone.
- Deep work: user says “go deep” or `/chain complex-task` / `/orchestrator` — expand stepwise, still cache-first per step.
- Full cache rebuild: `/chain cache-rebuild` only when user approves — never auto-trigger from cache-efficient.