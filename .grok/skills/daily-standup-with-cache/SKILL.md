---
name: daily-standup-with-cache
description: >
  Start a daily working session on project using the local cache + today's TODO + open concerns.
  This is the recommended prompt/skill for almost every normal development or review session.
argument-hint: "Optional focus, e.g. 'Frontend', 'Users', 'Filament work', 'schema', 'tests', 'valuations'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
---

# Daily Standup With Cache (Recommended Default Session Start)

**This is the skill you should invoke at the beginning of most sessions.**

## Step 0: Context envelope (preferred — all platforms)

**Token rule:** one script mints identity + MCP + branch + vault + open/next. Prefer this over loading the rest of this skill.

```bash
python3 scripts/session-context-envelope.py --write
# auto-switches to remote_last when clean; print compact CTX only
# CTX includes automatic orchestrator upgrade/init check (orch offer=…)
# see docs/reference/session-context-token-budget.md
python3 scripts/session-resume-brief.py check --json   # always — surface card when present
```

When envelope `resume_first=yes` and `expand` is only optional (`mcp_start` / `resume_card` / `orch_upgrade`):
**stop after printing the envelope + card + any orch upgrade offer**. Do not continue through
Steps 0a–5 unless the user asks for depth.

**Orchestrator upgrade (automatic at session-start):** if CTX has `orch offer=yes` or
`expand` includes `orch_upgrade`, surface **preview | apply | skip** (never auto-apply).
No separate step required on the lean path — the envelope already ran `session-orchestrator-check`.

## Step 0-legacy: Resume-first gate (if envelope script missing)

**Token rule:** when a fresh resume card exists, it replaces TODO/STATE/git re-discovery.

```bash
python3 scripts/session-resume-brief.py check --json
```

When `resume_first=yes` (see `.grok/skills/session-resume/references/resume-first.md`):

- Print `card` verbatim first; briefing cap **≤80 words** after the card.
- **Do not** Read full `TODO/*.md`, `STATE.md`, `VISION.md`, or narrate `git status`.
- `max_cache_files` from check (usually **0**; **1** only if cache caveat on card says stale).
- Still run: runtime detect, `resume-branch.sh`, security sweep script, vault verify (≤2 events).

When `resume_first=no`: full standup below (TODO, STATE, vault, cache spine).

## Step 0a: Runtime + MCP + manifest identity (mandatory — before git sync or cache reads)

Projects run in **DDEV**, **docker-compose**, or **local/host** (orchestrator template). Detect first — do not assume host-only MCP.

```bash
bash scripts/detect-project-runtime.sh --with-manifest-identity
# optional: bash scripts/detect-project-runtime.sh --json --with-manifest-identity
python3 scripts/check-project-manifest.py --json   # same identity gate (any model)
```

| `runtime` | MCP server (Grok `.grok/config.toml`) | App commands |
|-----------|--------------------------------------|--------------|
| `ddev` | `orchestrator-ddev` → `scripts/mcp-ddev-stdio.sh` | `ddev exec …` — never host php/artisan/composer |
| `docker-compose` | `orchestrator-host` (cache reads from repo root) | `docker compose exec <service> …` |
| `local` | `orchestrator-host` → `scripts/mcp-host-stdio.sh` | host shell (template repo) |

**Manifest identity (any model — required whenever the manifest is read):**

| `status` | Meaning | Agent action |
|----------|---------|--------------|
| `ok` | Manifest matches this repo (or is orchestrator source) | Proceed |
| `warn` | Partial mismatch | Surface issues; do not invent stack facts |
| `template_residue` | Still stock "Project Template" / generic stack on an app | **Warn operator**; customize `project-manifest.yaml` before trusting framework/runtime |
| `missing` | No manifest | Offer `orchestrator init` / upgrade |

MCP `get_project_manifest` returns the same gate under `identity` / `identity_briefing`.

**MCP rules:**
- Read `runtime.environment_manager` from manifest when present; file signals (`.ddev/`, compose file) are fallback.
- Surface `mcp_ready`, `ddev_running`, `compose_running`, `mcp_note`, and **`mcp_policy=dev_only`** in the briefing.
- **Develop only:** never start or recommend MCP on publicly hosted environments (DigitalOcean App Platform, public K8s, Heroku, etc.). When `mcp_env_safe=no` / `mcp_ready=blocked`, refuse and explain.
- When `mcp_ready` is not `yes`, **offer** numbered `mcp_start_options` (DDEV, Docker Compose + host stdio, local host) — never auto-start without user choice.
- **DDEV app repos:** enable `orchestrator-ddev`, disable `orchestrator-host` (see `mcp-server/config/mcp.grok.project.example.toml`).
- **Orchestrator template:** enable `orchestrator-host` only (no `.ddev/`).
- Apply `/ddev-local-runtime` for all project tooling when `runtime=ddev`.

## Step 0b: Local LLM / Ollama (optional BYOM)

Optional bring-your-own-model on the **operator machine** or via DDEV / docker-compose overlay. Not required for cloud AI (Grok/Copilot/Claude).

```bash
bash scripts/detect-ollama.sh
# optional: bash scripts/detect-ollama.sh --json
```

| Field | Meaning |
|-------|---------|
| `manifest_local_llm` | `none` (default) or `ollama` from manifest |
| `ollama_runtime` | Resolved target: `host`, `ddev`, or `docker-compose` |
| `ollama_binary` / `ollama_api` | CLI + API reachability |
| `local_llm_ready` | `yes` / `no` / `n/a` |

**Rules:**
- Read `runtime.local_llm` / `runtime.ollama_runtime` from the manifest.
- When `local_llm_ready=no`, surface `ollama_note` — offer optional install:
  - Auto: `bash scripts/install-ollama.sh` (or `bash scripts/install.sh --ollama`)
  - Force: `--target host|ddev|docker-compose`
  - Windows host: `.\scripts\install-ollama.ps1` or `.\scripts\install.ps1 -Ollama`
- Never auto-install Ollama during standup unless the user asks.
- Full guide: `docs/guides/local-ollama.md`

## Step 1: Remote branch resume (mandatory — never skip; before cache)

### Step 1a: All-projects remote sync (mandatory — multi-machine)

**Hard rule:** work spans multiple machines, so reconcile **every** git repo under `~/projects` with its remote at session start, not only the active project. Run first:

```bash
bash scripts/sync-all-projects.sh        # auto ff-only pull where safe
```

The script auto `git pull --ff-only`s clean, fast-forwardable repos and **only reports** diverged or behind+dirty ones (never touches them). Surface its "Attention" list and **offer** per-repo resolution (rebase / merge / stash) — never auto-merge or clobber. `--report-only` for a dry view. Include the one-line summary in the briefing.

### Step 1b: Active project branch resume

**Hard rule:** `/chain session-start`, `/daily-standup-with-cache`, and standup aliases **always** resolve the **latest remote branch worked on** (`origin/*` by committer date after `git fetch`) and **offer the user a switch** to it. Never auto-checkout.

Run from project root **before** synthesis:

```bash
bash scripts/sync-all-projects.sh        # multi-repo: auto ff-only pull clean behind branches
bash scripts/resume-branch.sh
git fetch origin --prune
git branch --show-current
git status -sb
# Latest remote branches (primary resume signal)
git for-each-ref refs/remotes/origin/ --sort=-committerdate \
  --format='%(refname:short)|%(committerdate:short)|%(authorname)|%(subject)' \
  | grep -vE 'origin/HEAD|origin/develop$|origin/master$' | head -8
# Local branches (secondary — may be behind or unpushed)
git for-each-ref refs/heads/ --sort=-committerdate \
  --format='%(refname:short)|%(committerdate:short)|%(subject)' | head -5
# Optional: recent pushes / open PRs
gh pr list --author @me --limit 5 2>/dev/null || true
```

Also read **Branch:** and **Resume branch (remote-last):** in the latest `TODO/*_TODO.md` (written by EOD `ddev-cleanup`).

**Pick resume target (required — per-operator first, then repo-wide):**

1. **`operator_last_branch`** from vault (`workspace_pointer` events, keyed by `git user.email`) — **this user's last branch** after EOD push on any machine. Prefer when `operator_pointer_found=yes` and branch exists on `origin`.
2. **`remote-last`** from git — newest `origin/<branch>` by committer date (repo-wide activity; may be a teammate's branch).
3. **TODO `**Branch:**`** / **Resume branch** — declared intent; note drift vs vault/script.

`remote-last` rules when used as fallback:
- Prefer `feature/*`, `fix/*`, `chore/*`, `docs/*`; exclude `develop`/`master` unless only activity.
- If TODO **Resume branch** differs from `resume-branch.sh`, prefer the script and note TODO drift.

**Also note:** `local-last`, `current`, `todo-branch`, `todo-resume-branch`.

**Sync status (lead with this — users want to know they are up to date):**

`scripts/resume-branch.sh` emits `sync_status` and `sync_message`. Surface **`sync_message` first** in the briefing:

| `sync_status` | Meaning |
|---------------|---------|
| `up_to_date` | Current branch matches upstream; say so clearly |
| `behind` | Other machine pushed work — offer `git pull --ff-only` |
| `ahead` | Up to date with remote; local commits not pushed |
| `diverged` | Needs explicit resolution |
| `dirty` | Uncommitted changes — resolve before pull |
| `no_upstream` | Cannot confirm sync |

Also report `remote_last_match=yes|no` (current branch vs latest repo activity).

**Current vs remote-last commit diff (mandatory — factor into switch offer):**

`resume-branch.sh` always emits a **HEAD vs `origin/<remote_last>`** comparison (even when you are not on that branch and have no local checkout of it):

| Field | Meaning |
|-------|---------|
| `vs_remote_last_behind` | Commits on remote-last **not** in current HEAD |
| `vs_remote_last_ahead` | Commits on current HEAD **not** in remote-last |
| `vs_remote_last_summary` | One-line human summary |
| `vs_remote_last_subjects` | Up to 3 commit subjects per side (`only_on_remote_last=…\|only_on_current=…`) |
| `switch_offer` | `yes` when `current` ≠ `remote_last` |

Include the diff counts (and subject samples when non-zero) in the switch prompt so the user can judge cost of switching vs staying.

**Integration branch (develop/master) lag (mandatory offer when behind):**

| Field | Meaning |
|-------|---------|
| `integration_branch` | `develop` if present on origin, else `master`/`main` |
| `integration_behind` / `integration_ahead` | Local integration ref vs `origin/<integration>` |
| `integration_ff_offer` | `yes` when behind only (clean ff) |
| `integration_offer_message` | Exact offer text |

When `integration_ff_offer=yes`, **offer** (never auto-run):

1. Preferred (no checkout): `git fetch origin <integration>:<integration>` (ff-only ref update)
2. Or: `git checkout <integration> && git pull --ff-only`

When diverged (`behind` and `ahead` both > 0), report only — no auto-ff.

**Ensure latest from the identified remote work branch (mandatory — covers pushes from other machines):**

After resume-branch + fetch + picking `remote-last`:

```bash
git fetch origin --prune
if [[ "$current" == "$remote_last" ]]; then
  # You are already on the latest remote activity branch: pull any work done elsewhere.
  git pull --ff-only origin "$remote_last" || echo "Note: ff-pull skipped or failed (dirty / diverged / no upstream)"
fi
```

This runs for the active project in addition to whatever sync-all-projects.sh did for the current checkout.

**If `current` ≠ `operator_last_branch` (vault):** offer switching to **your last branch** first (multi-machine resume).

**If `current` ≠ `remote-last`:** offer `remote-last` as *latest repo activity* — not as override when vault says you're on your own last branch and up to date. Always include `vs_remote_last_*` in the offer.

| | Branch | Role |
|---|--------|------|
| **Your last (vault)** | `operator_last_branch` | **primary for this user** across machines |
| **Remote last** | repo-wide newest push | team context; may be someone else |
| Current | where you are now | |
| TODO says | declared scope | |
| Integration | develop/master | base branch lag / ff offer |

End Step 1 with an explicit prompt (lead with **sync_message**, then **your last branch**, then remote-last **with diff**, then integration):

> **Sync:** `<sync_message>`
> **Your last branch (vault):** **`<operator_last_branch>`** (`<operator_last_ts>`) — on origin: yes/no.
> **Latest repo activity:** **`<remote-last>`** (`<date>`). Diff vs current: **`<vs_remote_last_behind>`** only on remote-last / **`<vs_remote_last_ahead>`** only on current. Subjects: `<vs_remote_last_subjects>`.
> You're on **`<current>`**. TODO: `<todo-branch>`.
> Switch to **your last branch** / **`<remote-last>`**? **`yes`** / branch / **`stay`** / **`no`**.
> **Integration:** `<integration_offer_message>` — **`ff develop`** / **`skip`** (when `integration_ff_offer=yes`).

When `sync_status=up_to_date` and `operator_resume_match=yes`, **confirm and continue** — do not pressure a switch; still surface remote-last diff + integration lag if non-zero.

- **`yes`** or matching branch name → `git checkout <branch>` then `git pull --ff-only origin <branch>` (the remote work is pulled).
- **`stay`** / **`no`** → continue on `current`; say why remote-last was not chosen if it differs from TODO.
- **`ff develop`** (or `ff master`) → run the preferred no-checkout ff command only after user confirms; never when diverged.

Then: branch purpose vs TODO scope; flag detached HEAD (always offer `remote-last`).

## Step 1c: Security sweep + Cyber Essentials (session-start standard)

After branch resume (and as part of `/chain session-start` security-hygiene step), run:

```bash
bash scripts/session-security-sweep.sh           # multi-repo secrets + active CSE + report file
# or: bash scripts/session-security-sweep.sh --active-only
# or: bash scripts/session-security-sweep.sh --json
```

**Mandatory user report:** the script writes `reports/security/session-sweep-YYYY-MM-DD.md` and
emits `report_path=…`. The session-start briefing **must** include a **Security sweep** section:

1. `overall=PASS|WARN|FAIL`
2. Path to the report (link/path the user can open)
3. Top findings (or “none”)
4. CSE warn count + offer `/chain cyber-essentials-review` when `cse_warns > 0`

| Signal | Action in briefing |
|--------|--------------------|
| `overall=PASS` | Cite report path; one-line clean summary |
| `overall=WARN` | Cite report path; list findings; continue session |
| `overall=FAIL` | Cite report path; surface secrets-guard failures first; do not ignore |

CSE is **lean/static** (`cyber-essentials-scan.sh`) — not a full certification report. Full depth lives in the written report + optional CE chain.

## Step 2: Vault brain brief + orchestrator version check (mandatory)

**Hard rule:** the secure vault graph (`reports/vault/events.jsonl`) is the **cross-session brain**.  
`workspace_pointer` (via `resume-branch.sh`) is **only** “which branch was I on” — it is **not** enough.

If Step 0 already ran `check` with `resume_first=yes`, **skip** vault todo-query open
resynthesis and STATE lessons dump — card already has open/done.

When `resume_first=no`, surface card via `read --compact` if present, then **always** run:

```bash
python3 scripts/session-vault-brief.py
# machine-readable:
# python3 scripts/session-vault-brief.py --json

# TODO-driven vault query (v1.5.0+) — open items from latest TODO/
python3 scripts/session-vault-todo-query.py

# Install / upgrade announcement (v1.4.2+) — always
python3 scripts/session-orchestrator-check.py --offer
# or: orchestrator check .
# Interactive host (TTY): python3 scripts/session-orchestrator-check.py --prompt
```

**Must surface in the briefing:**
- Ledger verify status (OK / issues)
- Last **≤5** learning events (`lesson`, `synthesis`, `codebase_knowledge`, …) as one-line bullets
- **Vault×TODO precedents** from `session-vault-todo-query.py` (cite before re-planning open work)
- Explicit rule: **do not re-plan or re-open work the vault already records as done**
- **Orchestrator version:** if not installed → announce `orchestrator init`; if upgrade available → **offer** (do not hide; do not auto-apply without user yes):
  1. **Preview** — `orchestrator upgrade . --if-available --no-pr` (dry-run when without `--yes`)
  2. **Apply** — `orchestrator upgrade . --if-available --yes --no-pr` (clean tree required)
  3. **Skip** — continue session on current template version
  - Also print `ORCHESTRATOR_UPGRADE_OFFER=yes|no` lines from `--offer`
  - Remote GitHub latest is probed unless `ORCHESTRATOR_NO_REMOTE_VERSION=1` (private repos: `GITHUB_TOKEN` / `GH_TOKEN`)

**Also read** `STATE.md` → `## Lessons → skills` and `## Verified facts` (spine; free). Compound-gate `state_lessons` reinforce the same.

If the vault script fails, ledger is missing, or `scripts/session-vault-brief.py` is not on this app yet:

- Say **once**: `Vault brief unavailable (no script / no ledger)` — then continue.
- Do **not** invent lessons.
- On apps: vault works after `orchestrator upgrade` with default selections (`grok` + `scripts`); ledger grows via loop-compound / EOD emit. Empty ledger ⇒ “brain empty,” not “skip vault forever.”

If `session-orchestrator-check.py` / `orchestrator check` is missing: say once and continue; recommend upgrading the template to ≥1.4.2.

## Step 2b: Wiki lean brief (Phase 2 — when wiki_policy.mode ≠ off)

After vault brief, **always** run (cheap; exits cleanly when mode=off or wiki missing):

```bash
python3 scripts/session-wiki-brief.py
# or MCP: wiki_status
# machine-readable: python3 scripts/session-wiki-brief.py --json
```

**Briefing rules:**

| Status | Action |
|--------|--------|
| `off` | One line: wiki disabled — continue |
| `missing` | Note scaffold/deploy selection `wiki` — continue |
| `ok` | Cite **≤5 log lines** + **≤5 open questions** + index section names. **Do not** full-read wiki pages |

MCP alternative: `wiki_status`, then `wiki_search_index` only if user asks a wiki question.

## Step 3: Load Core Cache (after vault — do not skip)

Honor `token_policy.max_cache_files_default` (default **2** extra docs after spine).

**MCP-first:** After Step 1 sync + Step 2 vault, prefer `get_project_manifest`, `read_cache_file`, `get_latest_todo` (use the MCP server from Step 0) before Read tool. Use `docs/codebase/SECTIONS.md` for section picks.

**Spine (does not count toward cap):**
1. Platform manifest (`.grok/project-manifest.yaml` for Grok; see `docs/reference/manifest.md`) — read `token_policy` only (grep `token_policy:` block)
2. `docs/codebase/README.md` — index section or first 80 lines
3. `docs/codebase/.codebase-freshness.txt` — **whole file only** (never `.codebase-scan.txt`)
4. Current daily TODO from `TODO/` (latest date file — branch + open items)
5. `.grok/memories/INDEX.md` — tier-1 table
6. Vault brief from Step 2 (already run) + `STATE.md` lessons/facts
7. Wiki brief from Step 2b (already run) — **not** full `wiki/` tree

**Forbidden on standup load:** `Read .codebase-scan.txt`, `scan.py`, `/read-codebase`, broad `Glob`/`Grep` without path scope, full `wiki/` dump.

**Pick ≤2 additional** (grep sections first; do not full-read registry/skills):
- `docs/codebase/CONCERNS.md` (default first pick)
- One of: `ARCHITECTURE.md`, task-specific cache doc, or one INDEX memory

## Step 4: Synthesise
Produce a short briefing for the user:
- **Vault lessons first** (what the brain says is already true — shipped features, policy, pitfalls)
- **Wiki brief** (if ok): recent log + open questions — do not re-plan wiki-recorded decisions without reading the page
- What the cache says the current priorities/risks are
- What today's TODO file says is in scope
- Any numbered CONCERNS items that are relevant
- **Shell/script discipline:** if CONCERNS §6 applies or last session had heredoc/syntax shell errors, remind user of `/script-not-shell` (write `scripts/` or `/tmp/agent-*`, never retry complex one-liners)
- **Runtime:** `detect-project-runtime.sh` result — DDEV/docker/local, MCP ready, and how to run app commands this session
- AI engineering maturity indicators (per the 8-stages model in /ai-engineering-maturity and copilot-instructions §11): e.g. shared .grok/ context adoption vs. drift, guardrail/MCP usage, evals/standards encoded in system, any "islands" in workflows. Note center of gravity and one concrete advancement opportunity.

## Step 5: Ask for Direction
End with a numbered list of suggested next actions based on the above.

**Token rule**: Do not read source files yet. Only read source after the user confirms the direction and you have absorbed the cache + TODO.

Cite every cache file you used in your response.

Full details in `.grok/prompts/daily-standup-with-cache.md`. Follow `.github/copilot-instructions.md`. Always consider AI maturity when the work involves Grok skills/agents/prompts or code generation.
