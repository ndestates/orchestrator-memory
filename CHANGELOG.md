# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.0] — 2026-08-02

**SemVer MINOR.** Product `VERSION` / npm / stamp / extension align at **2.2.0**.  
First GitHub Release train that ships **wheel + sdist + VSIX** with multi-surface slash registration (2.1.0 was never tagged as a public release).

### Added

- **`scripts/register-all-slash-commands.py`** — register every `.grok/skills` skill as a slash command on Grok · Claude · Cursor · Copilot · Gemini · ChatGPT; catalog at `docs/reference/slash-commands.md` + `chains/slash-catalog.yaml`
- **Cursor** `.cursor/commands/` for all skills (type `/chain session-start`, `/always-on-memory`, …)
- Claude commands for **all** skills (not only a hardcoded map); `sync_grok` always emits `.claude/commands/<name>.md`
- VS Code / Cursor extension **2.2.0**:
  - Palette titles are real slashes: **`/chain session-start`**, `/memory-brief`, `/setup`, `/quick-start`
  - Chat participant `@orchestrator` with `/session-start`, `/chain`, `/brief`, …
  - One-click CLI install (uv + published wheel), `SESSION_READY.md` + `MEMORY.md`
  - Loads `chains/slash-catalog.yaml` into the Command Hub
- Canonical host install docs use **v2.2.0** wheel URL

### Changed

- Product identity **2.2.0** (VERSION / stamp / package.json / extension / bundle-hashes)
- `register-project-skills` no longer re-tags template skills as `tier: app`
- Extension default `publishedCliVersion` = **2.2.0**
- Production-ship / installation docs: prefer published **2.2.0** wheel (not unreleased 2.1.0 URL)

### Fixed

- Broken install URL for non-existent `v2.1.0` wheel — users must use a **published** GitHub Release asset

## [2.1.0] — 2026-08-01

**SemVer MINOR** (backward-compatible features). Product `VERSION` / npm / stamp / extension align at **2.1.0**.  
Not a 2.0.x patch: Command Hub, vault+memory operator UX, and multi-channel docs are new surface area.

### Added

- VS Code / Cursor **Orchestrator Memory 2.1.0**: Command Hub, `/chain` + skill pickers, copy brief for Claude/Cursor/Copilot, Setup wizard, bundled **INSTRUCTIONS.md** (SQLite + vault dual-write), **Memory + vault storage** report, first-run read encouragement
- Product docs: host-first memory, always-on memory, production-ship, orchestrator-memory-product straplines
- Release path: GitHub Packages npm publish workflow; optional Marketplace package workflow (manage UI or Entra preferred over long-lived PAT)

### Changed

- Product identity **2.1.0** (VERSION / stamp / package.json / bundle-hashes)
- Extension semver policy documented in `extensions/vscode-orchestrator/CHANGELOG.md`

### Changed (prior unreleased notes retained below)

- Product identity 2.0.0 (VERSION/stamp/package/bundle)
- **MCP disabled by default** — not required for host CLI, chains, or cache-first file sessions.
  Session envelope reports `mcp=off@off`. Opt-in: `ORCHESTRATOR_MCP=1` or
  `runtime.mcp: dev_only` in project-manifest; then enable a server in `.grok/config.toml`.
  `orchestrator ensure` defaults to host-tools only (pass `--mcp` to ensure MCP venv).
  `install.sh` no longer auto-repairs MCP unless `--mcp`.

### Fixed


- resume-branch remote_last no longer resolves bare origin
- **App upgrade multi-branch blast** — `project_global_install` no longer broadcasts orchestrator
  commits onto **every local branch** or installs a post-checkout auto-commit hook by default.
  That behaviour thrashed large apps (e.g. Lightstone). **Opt-in only:**
  `ORCHESTRATOR_BRANCH_BROADCAST=1` and/or `ORCHESTRATOR_INSTALL_BRANCH_HOOK=1`.
  Kill-switch remains `ORCHESTRATOR_NO_BRANCH_SYNC=1`.

### Added


- Always-on memory agent (ingest/consolidate/query/serve; full model catalog + agent roster)
- **Host install: pnpm** — `bash scripts/install.sh --pnpm` and `--node` (prefer pnpm if on PATH, else npm); PowerShell `-Pnpm` / `-Node`. Same `@ndestates/orchestrator` host package as npm (→ Python CLI); machine-global, branch-independent.
- **`orchestrator upgrade --stash`** — if the app tree is dirty: `git stash push -u`, deploy, `stash pop`.

### Security


- Stronger with every update standard + SECURITY.md trust map
- **No cozy workspace tenet** — expertise (CS/law/"only we understand this") is not a trust boundary; workspace is assumed invadeable. Codified in `docs/internal/SECURITY-POSTURE.md` §0, AI content guardrails, CLAUDE.md, installed-apps guide, STATE lesson.
- **MCP threat scan** — exclude vendor trees (`.venv`, `site-packages`, …); first-party CRIT still fail-closed.

### Added

- **Host `self-upgrade` + `ensure`** — `orchestrator self-upgrade` refreshes the host CLI package (uv tool preferred, pip fallback; dry-run default, `--yes` to apply). `orchestrator ensure` wraps `ensure-mcp-host.sh` + `install-host-tools.sh` (`--check` / `--mcp` / `--host-tools`). Complements project-global install-persist; does not replace app `upgrade`.
- **Package-first host install** — `bash scripts/install.sh --uv-tool` installs the CLI via `uv tool install` (machine-global; survives git branch switches). Docs: host package vs in-app template table.
- **In-app install-persist fixed** — `scripts/orchestrator-branch-sync.py` is **stdlib-only** (no `orchestrator_cli` import; apps were no-op). New `orchestrator install-persist` establishes `orchestrator/installed` baseline + post-checkout + broadcast so template surfaces survive branch switches.
- **Versioning matrix** — `orchestrator version` prints host / template / app clocks (SSOT=`VERSION`); fixed false “not installed” on template source when CLI is a bundled package; lock writes normalize versions; docs `docs/reference/versioning.md`.

### Fixed

- **Tooling-tests / MCP threat scan with ripgrep** — `mcp-threat-scan.sh` used `rg -I` (`--no-filename`), so allowlist and vendor path filters never matched → 3 false CRIT hits on CI only (malware-lint self-strings). Now `rg -n -H` always emits paths; regression tests require path-bearing hits.
- **Model route (OSS first)** — `scripts/model-route-suggest.py` + `scripts/model-route/catalog.yaml` (open-weights required); skill `/model-route`; optional session-start step; guide `docs/guides/model-route-free-oss.md`. Offers stay|oss|install-oss|free-cloud; never silent-switch.

### Added

- **Chain `workstream-graph-demo`** — plan-named inventory diamond (workstreams + vault → code reduce → mermaid/JSON); alias of `multi-workstream-demo`. Optional `graph-example` step on `/chain multi-workstream` when asked (token-lean skip by default).

### Held (not in this release)

- **Freemium / license server / PayPal go-live** — still held; explicit unhold only
- **Open-source Apache + Patreon** — held_ready track; not auto-applied
- **Product agent graph (DIY runtime)** — parked; LangGraph/LangChain dropped for now

## [1.9.6] — 2026-07-27 (stable)

> **Stable patch** on 1.9.5 — skill catalog injection budget + hard token stop.  
> Install: `orchestrator upgrade . --from-github v1.9.6 --yes --no-pr --quiet` (or local path until tag).  
> Template identity: **`VERSION` / stamp = `1.9.6`**.

### Fixed

- **Grok skill catalog bloat** — `description` frontmatter capped at 220 chars
  (`token_policy.skill_description_max_chars`). Grok injects name+description for
  every skill into system_reminder messages; long descriptions were a primary driver
  of multi‑MB / ~1M+ token sessions when re-injected each turn.
- **Lint + auto-fix** — `scripts/lint-skill-descriptions.py` (+ `--fix`);
  tests in `tests/test_lint_skill_descriptions.py`.
- **Hard stop policy** — `hard_stop_context_tokens: 128000`, `agent_stop_on_critical: true`.
  Token-usage-meter CRITICAL / auto-compact fail / API budget 400 = stop tools, handoff only.
- **Docs** — `docs/reference/skill-description-budget.md`.

### Added

- **`orchestrator upgrade|init --quiet` / `-q`** — suppress per-file NEW/UPDATE/CONFLICT
  lines; keep one-line summary with stats (agent-safe; cuts tool-output token cost).

### Changed

- All `.grok/skills/**/SKILL.md` descriptions shortened to budget (synced to GitHub/Copilot surfaces).
- skill-creator: description budget is mandatory when drafting skills.

## [1.9.5] — 2026-07-24 (stable)

> **Stable patch** on 1.9.4.  
> Install: `orchestrator upgrade . --from-github v1.9.5 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.5`**.

### Added

- **Project-global install** — after init/upgrade, maintain `orchestrator/installed`
  baseline, **broadcast** orchestrator paths to all local branches, and install a
  **post-checkout** hook so new/other branches auto-sync without user thought.
  Path-limited restore (not a full feature-branch merge). Respects customized
  deploy-state paths. Opt out: `ORCHESTRATOR_NO_BRANCH_SYNC=1`.

## [1.9.4] — 2026-07-24 (stable)

> **Stable patch** on 1.9.3.  
> Install: `orchestrator upgrade . --from-github v1.9.4 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.4`**.

### Fixed

- **Install persists on the working branch** — with `--no-pr` (default for app
  upgrades / session auto-upgrade), init/upgrade commits on the **current** branch
  instead of leaving files only on a disposable `chore/orchestrator-*` branch.
  PR mode still uses a chore branch, then **merges back** to the starting branch
  so checkout switches keep orchestrator surfaces.

## [1.9.3] — 2026-07-24 (stable)

> **Stable patch** on 1.9.2.  
> Install: `orchestrator upgrade . --from-github v1.9.3 --yes --no-pr`  
> Also refresh host CLI: `pip install -U orchestrator==1.9.3` (or reinstall editable).

### Fixed

- **`orchestrator version` stale CLI identity** — in a dev checkout, CLI version
  now follows **`VERSION`** (SSOT) instead of lagging pip metadata, so you no longer
  see `orchestrator 1.9.1 (template 1.9.2, dev checkout)` after a template bump.
- **Version report** — shows **app lock** from `.orchestrator-version` when present;
  notes stale pip metadata and CLI-vs-app drift with upgrade hints.

### Added

- **CLI hygiene on init/upgrade** — after a successful deploy, reinstall host CLI
  (`pip install -e` from template root, or `pip install orchestrator==X.Y.Z`) so pip
  metadata matches the template. Opt out: `ORCHESTRATOR_SKIP_CLI_HYGIENE=1`.

## [1.9.2] — 2026-07-24 (stable)

> **Stable patch** on 1.9.1.  
> Install: `orchestrator upgrade . --from-github v1.9.2 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.2`**.  
> Session-start on apps: auto-upgrade from GitHub when newer (stash WIP if dirty;
> skip customized scripts; preserve project-manifest). Opt out:
> `ORCHESTRATOR_SESSION_AUTO_UPGRADE=0`.

### Added

- **Session-start remote_last-first** — fetch → switch/pull team tip → **then** resume card
- **Situation brief** — where we are / in-flight / vault+wiki repetition gate
  (`session-situation-brief.py`, fingerprint cache)
- **Spin-up bundle** — one model-visible artifact (`session-spinup-bundle.py`)
- **Guardrails check** — `session-guardrails-check.py` + guide
  `docs/guides/prompt-injection-installed-apps.md`
- **Security sweep fingerprint cache** — re-scan when security-relevant tree changes
- **Vault `session_startup`** events for startup-method double-check
- **Version alignment** — `scripts/check-version-alignment.py` (pre-release-aware compare)
- **Vector probe** — report-only; **reject** embedding DB for this meta-repo

### Fixed

- **Registry YAML** — skill_args colon broke compose/CI (`tooling-tests`)
- **Pre-release version compare** on session-orchestrator-check (pre.5 > pre.3; final > pre)
- **Auto-upgrade on dirty trees** — soft-clear session noise + stash WIP, then apply, then restore

## [1.9.1] — 2026-07-23 (stable)

> **Stable patch** on 1.9.0.  
> Install: `orchestrator upgrade . --from-github v1.9.1 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.1`**.

### Added

- **MCP smoke** — `scripts/mcp-smoke.sh` + `orchestrator_mcp.smoke` (stdio `list_tools` +
  `health_check`); CI `mcp-security` runs smoke; host-is-client docs in `mcp-server/README.md`
- **Session-start MCP handshake** — when host stdio MCP looks ready, probe smoke; set
  `mcp_ready=fail` + repair offer when handshake fails
- **`/top-class-website-designer`** — PhD-level full-stack web architect skill (Python + MySQL
  theory, HCI, security); registered on Grok/Claude/Copilot/GitHub surfaces + agent stubs
- **Design note** — `docs/internal/MCP-RECOMMEND-TOOLS-SCHEMA.md` (future static `recommend_tools`)

## [1.9.0] — 2026-07-23 (stable)

> **Stable release** (not a pre-release). Replaces pre.1–pre.5 for production upgrades.  
> Install: `orchestrator upgrade . --from-github v1.9.0 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.0`** (no `pre.*`).

### Fixed

- **Session-start last branch** — always `git fetch` + target **remote_last** (newest
  `origin/*` feature tip by committer date). Never stay on a stale vault
  `operator_last_branch` when remote activity is newer. Dirty WIP still blocks switch.
- **Vault pointer refresh** — after a successful `--apply` switch, emit workspace
  pointer for the new branch so the next session is not re-stuck.
- **Envelope pickup** — surfaces `remote_last` as last-worked; reports `vault_stale`
  when vault and remote-last disagree.

### Includes (from 1.9.0-pre.1 … pre.5)

- Multi-workstream (all hosts), numbered selectors, activate/park, diamond/serial,
  worktrees, guard, prompts, web-cache-expert, deploy-bundle multi-workstream scripts,
  resume-first cards, orchestrator check-on-session-start

## [1.9.0-pre.5] — 2026-07-22 (pre-release · install multi-workstream scripts)

> **Stable remains [1.8.9](#189--2026-07-21).** Opt-in only.  
> Install: `orchestrator upgrade . --from-github v1.9.0-pre.5 --yes --no-pr`  
> Template identity: **`VERSION` / stamp = `1.9.0-pre.5`**.  
> **Prefer this over pre.4** if you need worktree/prompts/guard CLIs on apps.

### Fixed

- **Deploy bundle** — multi-workstream runtime scripts were missing from the default
  `scripts` selection, so `orchestrator upgrade` installed the skill/chains but not:
  `workstream.py`, `workstream_worktree.py`, `workstream_guard.py`,
  `workstream_prompts.py`, `workstream_recommend.py`, `workstream_graph_example.py`,
  `sync-multi-workstream-surfaces.py`
- Ships `reports/sessions/workstreams.example.yaml` + session/agent-graphs scaffolds
- Test: `test_scripts_selection_includes_multi_workstream_runtime`

### Includes (from pre.1–pre.4)

- Multi-workstream all hosts, numbers/activate, diamond, worktrees, serial, guard,
  prompts, web-cache-expert, 90 unit tests

## [1.9.0-pre.4] — 2026-07-22 (pre-release · worktrees + prompts + tests)

> **Stable remains [1.8.9](#189--2026-07-21).** Opt-in only.  
> Install: `orchestrator upgrade . --from-github v1.9.0-pre.4 --yes --no-pr`  
> Template identity: **`VERSION` / stamp = `1.9.0-pre.4`**.

### Added

- **Git worktrees** — `/multi-workstream worktree list|add|remove|status` for feature-branch isolation
  under the parent of the main repo (`…/<repo>-ws-<slug>`). Safeguards: no held/parked without
  `--force`, no protected branches, path jail, no merge/push
- **Serial plan** — `/multi-workstream serial` (primary-only alternative to diamond)
- **Integrity guard** — `/multi-workstream guard` (primary active, protected branch, worktree path)
- **Operator prompts** — `/multi-workstream prompts|ready|status` (merge-ready, ready-for-PR, WIP, frozen)
- **Tests** — 90 pytest cases for selectors, worktrees, guard, prompts, Shape B recommend
  (`tests/test_workstream*.py`)

### Fixed

- Worktree `_run` resolves repo root at call time; clearer hint when branch already checked out

### Changed

- **LangGraph / LangChain** — dropped for this cycle; `product_graph` stays parked DIY-only
- Alternatives + safeguards guide: `docs/guides/multi-workstream/alternatives-and-safeguards.md`

### Includes (from pre.1–pre.3)

- Multi-workstream all AI hosts, numbered selectors, activate/all, diamond Shape B, web-cache-expert

## [1.9.0-pre.3] — 2026-07-22 (pre-release · multi-workstream numbering)

> **Stable remains [1.8.9](#189--2026-07-21).** Opt-in only.  
> Install: `orchestrator upgrade . --from-github v1.9.0-pre.3 --yes --no-pr`  
> Template identity: **`VERSION` / stamp = `1.9.0-pre.3`**.

### Added

- **Numbered workstream selectors** — list shows `#`; use `1`, `2,3`, `1-3`, or `all`
- **activate / unhold / park / add** — open held tracks; register new ids
- Setup guide: `docs/guides/multi-workstream/setup.md`

### Includes (from pre.1–pre.2)

- Multi-workstream all AI hosts, diamond Shape B recommend, web-cache-expert
- Release gate full pre-string match; registry webmcp template fix

## [1.9.0-pre.2] — 2026-07-22 (pre-release · multi-workstream + web-cache)

> **Stable remains [1.8.9](#189--2026-07-21).** Opt-in pre-release only.  
> Install: `orchestrator upgrade . --from-github v1.9.0-pre.2 --yes --no-pr`  
> Template identity: **`VERSION` / stamp / package.json = `1.9.0-pre.2`** (not bare `1.9.0`).

### Added

- **Web cache expert** — `/web-cache-expert` · `/chain web-cache-review` for HTTP/CDN/image/document
  caching and refresh architecture (Laravel-first, multi-stack). Guide:
  `docs/guides/web-cache-architecture.md`. Not AI token `/cache-efficient`.
- References: http-cache-headers, laravel-cache-stack, image-document-cdn, cache-refresh-playbook
- All AI surfaces (Grok · Claude · Copilot · ChatGPT · Gemini · Cursor)

### Fixed

- **Release workflow** — pre-release tags require full VERSION match (`1.9.0-pre.2` == `v1.9.0-pre.2`); auto `--prerelease`
- **Template version display** — stamp shows full pre-release label (users were seeing bare `1.9.0`)
- **Tooling Tests / registry compose** — `webmcp-beta` restored to `registry.template.yaml` so
  compose(template, app) matches `registry.yaml`

## [1.9.0-pre.1] — 2026-07-22 (pre-release · multi-workstream)

> **Stable remains [1.8.9](#189--2026-07-21).** This is a **GitHub pre-release** only.  
> Opt-in apps: `orchestrator upgrade . --from-github v1.9.0-pre.1 --yes`  
> Do not treat as Latest stable.

### Added

- **Multi-workstream** — day-scale tracks (`reports/sessions/workstreams.yaml`), slash-first
  `/multi-workstream` on **all** AI hosts (Grok · Claude · Copilot · ChatGPT · Gemini · Cursor)
- **Shape B diamond recommend** — `/multi-workstream diamond` · `/chain multi-workstream-diamond`
  (safe multi-lane plan from workstreams + TODO; **no auto-exec**; preserve primary; no unhold)
- Shared implementation contract + sync: `docs/guides/multi-workstream/IMPLEMENTATION.md`,
  `scripts/sync-multi-workstream-surfaces.py`
- Per-LLM guides under `docs/guides/multi-workstream/`
- Runtime: `scripts/workstream.py`, `workstream_recommend.py`, `workstream_graph_example.py`
- Session-start lean `ws primary=…` line in context envelope
- **WebMCP beta** (experimental, optional/parked) — separate product; not required for multi-stream

### Changed

- Multi-workstream decoupled from WebMCP (WebMCP may be parked only)
- Operator UX is slash-first; scripts are agent implementation

## [1.8.9] — 2026-07-21

### Fixed

- **Template stamp lag** — `scripts/orchestrator-template-version` lagged at 1.8.7 while
  `VERSION` was 1.8.8; stamp now mirrors `VERSION` and is enforced at release
- `node scripts/npm/sync-version.js` writes **package.json + stamp** from `VERSION`
- Pre-release gate + Release workflow: fail if stamp or package.json ≠ `VERSION`

## [1.8.8] — 2026-07-21

### Added

- **Host tools installer** — `scripts/install-host-tools.sh` / `.ps1` for **ripgrep (`rg`)**
  (apt/dnf/brew/…); `install.sh --host-tools`; DDEV `webimage_extra_packages` snippet +
  `mcp-server/ddev/Dockerfile.tools`; CI tooling-tests installs `rg`
- **MCP ensure + reliable host launcher** — `scripts/ensure-mcp-host.sh` (uv preferred);
  `mcp-host-stdio.sh` auto-repairs venv; `detect-project-runtime` auto-repairs on session-start;
  `install.sh --mcp`; Grok/Cursor launchers no longer depend on fragile empty git ROOT
- **ChatGPT / OpenAI surface** — `.chatgpt/` (manifest, instructions, session prompt, MCP examples);
  deploy selection `chatgpt`; `ORCHESTRATOR_AI_PLATFORM=chatgpt|openai|codex`
- **Multi-host MCP client examples** — Claude, Copilot (VS Code `servers` shape), Gemini,
  ChatGPT host/DDEV configs under surfaces + `mcp-server/config/`
- **Production guide** — `docs/guides/multi-platform-mcp-and-host-tools.md` (+ docs hub indexes)

### Changed

- Platform surface map includes ChatGPT; all hosts list sibling surfaces in `do_not_prefer`
- Manifest sync targets include `.chatgpt/project-manifest.yaml`
- Deploy `mcp` selection ships ensure/launch scripts + multi-platform examples
- Installation / quickstart / per-app-upgrade / README / platform-surfaces docs for production operators
- CSE scan skip messages point at `install-host-tools.sh` when `rg` missing
- DDEV `Dockerfile.mcp` installs **ripgrep** with MCP Python deps

### Fixed

- Residue amend: project title prefers **directory slug** over stack profile marketing title
  (`Python Flask App` → `Mailchimp` for dir `mailchimp`) — CI `test_amend_template_residue`

## [1.8.7] — 2026-07-20

### Added

- **Context-window literacy** guide — `docs/guides/context-window-literacy.md` (+ index);
  multi-session / vector DB abandoned for orchestrator (mailchimp-only multi-session)
- **Session-start auto-switch** to `remote_last` when the working tree is clean
  (`resume-branch.sh --apply`; envelope default apply)
- **Always check + resume-card** at session-start (surface card even when stale)
- **Rich resume cards** at session-end and eod-shutdown (`write --rich`; HEAD, remote-last,
  ver, open/next/done)
- **Session-start automatic upgrade check** — envelope always runs
  `session-orchestrator-check` (`orch kind/offer` on CTX); offer preview|apply|skip only
- **Project-manifest install policy** — never overwrite customized app manifests;
  seed/amend stack-aware identity on new or template-residue projects
  (`scripts/_engine/manifest_bootstrap.py`; hard `is_never_deploy` protect)

### Changed

- Session envelope / standup / ddev-cleanup / chain registry: auto-switch + mandatory
  check/card; EOD vault step commits vault/resume if dirty after emit
- Stack profiles gain `manifest_stack` (laravel, python-flask, facebook-stats, google-stats)

### Fixed

- Manifest path protect: do not use `str.lstrip("./")` (broke `.github/...` matching)
- Resume-branch: no `checkout -B`; pull only when behind; dirty always blocks switch
- EOD: warn when vault/resume leave porcelain dirty after emit

### Security

- Bug hunt + CSE code slice for this branch: `reports/bugs/2026-07-20-bug-hunt-session-manifest.md`,
  `reports/security/cyber-essentials/2026-07-20-session-manifest-cse.md`

## [1.8.6] — 2026-07-18

### Added
- **`orchestrator upgrade --if-available [--yes]`** — check-then-upgrade; dry-run without `--yes`
- **`--from-github [TAG]`** — materialize GitHub release into `~/.cache/orchestrator/releases/` and upgrade from it
- Session check: `--offer` / `--prompt`; GitHub Releases latest version probe
- Profile inference for dry-run when `stack.profile` missing

### Changed
- `session-orchestrator-check.py` + standup skill surface preview|apply|skip
- Docs: per-app-upgrade + installation check/upgrade paths


## [1.8.5] — 2026-07-18

### Added
- **Code review skill** (template-owned): process + PHP/MySQL/Python stack lens + local-orchestrator checks
- Wired to **existing strict maintainability** bar (`references/strict-maintainability.md` / code judo)
- Agent, Claude command, chain `code-review` + `delivery` review step
- Source article: `docs/reference/code_review_article.md`

### Changed
- `/chain code-review` and delivery use `code-review` skill (not bare bug-hunter alone)
- Optional bug-hunter only when deep/blocking; security still gated on auth/secrets paths


### Added

- **Wave absence guard** — `tests/test_wave_absent.py` asserts fleet wave scripts,
  `scripts-fleet` bundle selection, and `orchestrator wave` CLI stay deleted.

### Fixed

### Changed

- **Fleet wave deploy removed permanently (Phase A)** — deleted all
  `scripts/*wave*` fleet entrypoints, `wave-inventory.yaml`, fleet compound
  scripts, and the `orchestrator wave` CLI. Per-app only:
  `orchestrator init|upgrade`. Docs and orchestrator-deploy skill updated;
  historical log retained at `docs/guides/wave-deploy-log.md`.

### Security

## [1.8.4] — 2026-07-17

### Added

- **Session context envelope (all platforms / all apps)** — `session-context-envelope.py`
  mints a fixed-size CTX (identity, MCP dev-only, branch, vault, sec, open/next,
  **pickup/continue-where-left-off**, `ver` + `behind_develop`, **platform surface**);
  thin skills/rules for `.grok` `.claude` `.copilot` `.github` `.gemini` `.cursor`;
  session-start must always surface `ask:` so the user can resume last work if they wish
  (never auto-checkout); each host uses **only its tree** (Grok→`.grok`, Claude→`.claude`, …)
  per `docs/reference/platform-surfaces.md`; token budget doc
  `docs/reference/session-context-token-budget.md`
- **Manifest identity gate (any model)** — `scripts/check-project-manifest.py` +
  `_engine/manifest_identity.py`: when reading `project-manifest.yaml` (file or MCP
  `get_project_manifest`), verify it describes *this* repo and is not stock
  orchestrator "Project Template" residue; surface `template_residue` / `warn`;
  wired into session-start, load-cache, standup, CLAUDE.md; MCP returns `identity`
- **MCP session status + develop-only policy** — `detect-project-runtime.sh` emits
  `mcp_policy=dev_only`, `mcp_env_safe`, and numbered **start options** (DDEV /
  Docker Compose / host stdio) when not ready; blocks public/prod hosts (DO App
  Platform, K8s, Heroku, …); `_engine/mcp_runtime_policy.py`; never for public hosting
- **Platform surface map** — `docs/reference/platform-surfaces.md` +
  `scripts/_engine/platform_surface.py`; tests for per-host manifests/entrypoints
- **Internal maintainer docs** (not shipped in npm/deploy) — `docs/internal/` security
  posture, codebase map, skills/chains catalogs

### Security

- Expanded `tests/test_content_guardrails.py` (injection, toxic, strict block, E2E payloads)

## [1.8.3] — 2026-07-16

### Added

- **AI content guardrails (defense in depth)** — `untrusted_text.py` (prompt injection + PII +
  toxic scrub), `/ai-content-guardrails` skill, `.grok/references/ai-content-guardrails.md`,
  agent footers (84 agents), MCP `read_bounded` fencing, vault `scrub_for_ai_context`;
  `security_policy` in manifest; synced to Grok/Copilot/Claude/Cursor/Gemini
- **`scripts/session-resume-brief.py`** — cross-project resume card (Lightstone-style) for
  `/chain session-end` and `/chain session-start`: project, branch + dirty detail, done/open
  from TODO, cache caveat; wired into `session-end-checkpoint.py` and deploy bundle
- **Resume-first mode** — `check` subcommand + `/session-resume` skill: when fresh
  `resume-*.md` exists, session-start skips TODO/STATE/VISION re-reads (`max_cache_files`
  usually 0); synced to `.grok/`, `.github/`, `.claude/`, `.copilot/`; `token_policy.resume_first_max_hours`
- **LLM Wiki (Karpathy pattern) Phases 0–4:** `wiki/` + `raw/`, `/llm-wiki`, chains
  `wiki-ingest` / `wiki-query` / `wiki-lint` / `wiki-lint-watch`, deploy selection `wiki`,
  session-wiki-brief, wiki_lint_check, MCP `wiki_status` / `wiki_search_index` /
  `wiki_read_page`, guide `docs/guides/llm-wiki.md`, pilot meta-knowledge pages
- VS Code Marketplace extension scaffold (vscode-extension/) wrapping npm/CLI
- Port npm package (@ndestates/orchestrator) and licensing_policy/first_party from #117 residual; keep #116 license-server and fail-closed wave

### Fixed

- CSE scan excludes virtualenvs (`.venv` / `site-packages`) so local MCP deps do not fail pre-release gate
- Regenerate bundle hash stamp after guardrails edits to sandbox.py and vault.py
- MCP host uv bootstrap; loop_compound import path; vault content_hash dedupe
- Deploy session-vault-brief + vault pointer/emit scripts in app scripts selection so session-start vault works after orchestrator upgrade
- Session-start now mandates vault brain brief (session-vault-brief.py); standup used only workspace_pointer before
- **`session-security-sweep.sh` defaults to active app only** — no longer walks
  `~/projects/*` on session-start (fleet was wrong scope for app hygiene and hung on
  huge dirty trees e.g. frontend-demo). Opt-in: `--all-repos` / `--fleet`. Dirty-path
  collection caps at 40 files while iterating (not after).

### Changed

- Standing stop on fleet wave install; mailchimp/google-stats 1.8.2 wave fail root-caused (missing lock + git clean wiped bootstrap)
- session-security-sweep defaults to active app only; fleet opt-in via --all-repos; dirty-path cap while collecting

### Security

- P0+P1 prompt-injection: untrusted_text + vault/MCP safe reads
- AI content guardrails at vault, session brief, and MCP read boundaries
- Bug-hunt scan: prompt-injection surfaces (vault/MCP/TODO); report reports/bugs/2026-07-14-prompt-injection.md

## [1.8.2] — 2026-07-14

Patch release of the 1.8.1 candidate (never tagged) plus security-scan fixes.

### Added

- Restored **optional Local Ollama (BYOM)** multi-runtime install: host, DDEV add-on, and
  docker-compose overlay (`docs/guides/local-ollama.md`, `scripts/install-ollama*.sh`,
  `scripts/install-ollama.ps1`, `scripts/detect-ollama.sh`).
- Bootstrap flags: `bash scripts/install.sh --ollama`, `.\scripts\install.ps1 -Ollama`.
- Manifest fields `runtime.local_llm` and `runtime.ollama_runtime` (default `none` / `auto`).
- Deploy-bundle ships Ollama detect/install scripts with the `scripts` selection.
- `session-security-sweep.sh` listed in deploy-bundle (fixes apps missing the session report).
- **`scripts/pre-release-gate.sh`** — mandatory pytest + security suite before every release
  (wired into `release.yml`; no tag without green).

### Fixed

- Cyber Essentials scan no longer self-matches pattern strings in scanner sources or
  `reports/security/*` (false WARN flood on session-start).
- Session security sweep only counts real `WARN:` lines and path:line hits (not APP_DEBUG
  text inside the scan script).
- Flaky `test_find_existing_live_when_gh_available` skips empty gh output.

### Changed

- Session-start / daily-standup Step 0b again detects Ollama and **offers** optional install
  (never auto-installs without user request).
- Release workflow: single **pre-release-gate** step (tests required).

## [1.8.0] — 2026-07-14

### Added

- Session-start hygiene: `resume-branch.sh` emits current↔remote-last commit diff
  (`vs_remote_last_*`) and integration (develop/master) ff offer fields; new
  `scripts/session-security-sweep.sh` multi-repo secrets guard + lean Cyber
  Essentials scan with mandatory report at `reports/security/session-sweep-YYYY-MM-DD.md`;
  `session-start` chain step `security-hygiene` (required; briefing must cite report).

### Security

- Session-start multi-repo secrets + lean Cyber Essentials sweep
  (`scripts/session-security-sweep.sh`); report path is mandatory in the user briefing.

## [1.7.0] — 2026-07-11

### Performance

- Vault `append_event` content_hash cache; `verify_ledger` O(n) parent/relation sets.
- MCP registry mtime cache + O(1) chain id lookup (`get_chain_by_id`).
- Token monitor single-pass session parse; compound single STATE read; unclosed-report scan cap 20.
- Skill-governance critical-only default; malware-lint path allowlist short-circuit.
- CLI `create_branch` reuses existing branch (upgrade re-run).

### Includes 1.6.1

- Malware Phases 2–4 (bundle hash, skill governance, vault injection filter, wheel SHA256SUMS).
- MCP host uv bootstrap; compound import + ledger dedupe.

## [1.6.1] — 2026-07-11

### Security

- Bundle hash stamp + `--verify-bundle`; skill tool-governance lint; vault prompt-injection filter.
- Release attaches `SHA256SUMS.txt` + `bundle-hashes.json`.

### Fixed

- MCP host stdio bootstrap without python3-venv (uv fallback).
- `loop_compound` import path; vault append idempotent on content_hash.

## [1.6.0] — 2026-07-11

### Security

- **Fail-closed MCP/agent threat scan** — `scripts/mcp-threat-scan.sh` exits 1 on critical hits
  (allowlist in `scripts/security/threat-scan-allowlist.txt`).
- **Malware / hostile-content lint** — `scripts/orchestrator-malware-lint.py` + CI
  `.github/workflows/security-malware.yml`; wired into tooling-tests and release gates.
- **CODEOWNERS** for high-risk paths (scripts, workflows, hooks, MCP, CLI).
- Docs: `docs/operations/security-malware-defence.md`; CONCERNS §12.

## [1.5.1] — 2026-07-11

### Added

- **`/chain session-end`** — mid-day pause (not EOD). Dirty git OK; no ddev stop; no
  tomorrow TODO. Writes `reports/sessions/pause-*.md`, TODO resume note, light vault
  pause lesson + workspace pointer. Script: `scripts/session-end-checkpoint.py`.
- Daily workflow documents session-end vs eod-shutdown.

## [1.5.0] — 2026-07-11

### Added

- **Vault learning expansion (A/B/C)** — see `docs/guides/vault-learning-expansion.md`
  - **A Guaranteed EOD emit** — `eod-vault-emit.py` always writes (rich or heartbeat); eod-shutdown
    `vault-emit` step is **required**
  - **B TODO-driven vault query** — `session-vault-todo-query.py` at session-start/standup
  - **C CI failure emit** — `vault-emit-ci-failure.py` + example workflow under `docs/examples/`
- Deploy-bundle ships the new scripts with the `scripts` selection.

### Changed

- EOD vault emit no longer skips quiet days by default (use `--skip-if-empty` for legacy).
- Standup / session-start spine: brief → TODO query → version check.

## [1.4.3] — 2026-07-11

### Fixed

- **session-orchestrator-check in apps / ddev** — script is stdlib-only; no longer requires
  `pip install orchestrator` or `PYTHONPATH=src`. Compares `.orchestrator-version` to
  `scripts/orchestrator-template-version` (deployed with the template). Optional: env
  `ORCHESTRATOR_TEMPLATE_VERSION`, sibling `../orchestrator/VERSION`, or full CLI if present.

### Added

- `scripts/orchestrator-template-version` stamp file (mirrors `VERSION`) in deploy-bundle.

## [1.4.2] — 2026-07-11

### Added

- **Automatic install/upgrade announcement** — `orchestrator check` and CLI auto-check on most
  commands compare `.orchestrator-version` to the template `VERSION` and announce when not
  installed or when a newer template is available.
- **Session-start version check** — `scripts/session-orchestrator-check.py` (standup + session-start
  chain); surfaces init/upgrade prompts in the daily briefing.
- Exit codes for automation: `check` returns 2 (upgrade available), 3 (not installed).
- Opt-out: `ORCHESTRATOR_NO_UPDATE_CHECK=1`.

### Documentation

- Per-app upgrade guide: automatic checks at session-start and CLI usage.

## [1.4.1] — 2026-07-11

### Fixed

- **sync root pin during init/upgrade** — `scripts/sync_grok_to_github_claude.py` now calls
  `set_template_root()` **before** importing `sync_grok`, so `GITHUB`/`GROK` paths bind to the
  **app** tree. When `PYTHONPATH` included the orchestrator checkout, sync previously wrote under
  the template and failed with `relative_to` errors; `orchestrator init` rolled back.
- **customize subprocess env** — post-deploy sync runs with `PYTHONPATH=<app>/scripts` only so a
  second orchestrator checkout cannot win on imports.

### Documentation

- Per-app upgrade guide notes 1.4.1 requirement for reliable CLI init/upgrade from a template checkout.
- RELEASE_NOTES for v1.4.1.

## [1.4.0] — 2026-07-11

### Added

- **npm package** `@ndestates/orchestrator` — `package.json`, `bin/orchestrator.js`, `scripts/npm/*` (postinstall installs Python CLI).
- **Session vault brief** — `scripts/session-vault-brief.py`; session-start loads vault lessons (not only branch pointer).
- Vault scripts in deploy-bundle `scripts` selection (`session-vault-brief`, workspace pointer, eod emit, learning watch, backfill, `reports/vault/.gitkeep`).
- Licensing policy modules: `licensing_policy`, `first_party`, `defaults` + tests.
- **Per-app upgrade guide** — `docs/guides/per-app-upgrade.md` (fleet wave abandoned as default).
- `LICENSE` and pyproject license metadata.

### Changed

- Installers: `install.sh --npm`, `install.ps1 -Npm`; installation docs for npm.
- Standup / `session-start` chain: mandatory vault brain brief.
- Template deploy docs emphasize per-app `orchestrator upgrade` only.

### Fixed

- Session agents re-planning finished installer/cease-wave work; spine + vault record PR #116 truth; #117 npm residual ported without removing license-server.

## [1.3.0] — 2026-07-09

### Changed

- **Cease fleet wave as default install path** — `auto_deploy: false`, policy guards, and
  `orchestrator wave` blocked unless `ORCHESTRATOR_WAVE_DEPLOY_APPROVED=1`. Preferred path:
  per-app `orchestrator init` / `orchestrator upgrade` (see `docs/getting-started/installation.md`).
- Bootstrap installers: `scripts/install.sh --cli` and Windows `scripts/install.ps1` (`-Cli`)
  for package install of the `orchestrator` CLI.

### Added

- Full installation guide: `docs/getting-started/installation.md` (Linux/macOS, Windows PowerShell, pip, per-app CLI).
- Licensing guide: `docs/reference/licensing.md` (CLI + MCP license gate, fail-open default).
- Windows PowerShell bootstrap installer: `scripts/install.ps1`.
- **Reference license validate server** — `orchestrator license-server` /
  `src/orchestrator_cli/license_server.py` implements `POST /api/licenses/validate`
  (allowlist / first-party / dev-accept-any); script `scripts/license-validate-server.sh`.

### Security

- MCP server hardened: HTTP transport fails closed without `ORCHESTRATOR_MCP_API_KEY`
  (non-loopback always requires a key; keyless loopback only via `--allow-insecure-http`);
  request-time bearer auth wired via streaming-safe `BearerASGIMiddleware`; stdio warns
  and stays allowlist-bounded.
- Added `mcp-server/tests/test_security.py` (sandbox allowlist, auth, fail-closed gate)
  and `.github/workflows/mcp-security.yml` (pytest + threat scan on `mcp-server/**`).


## [1.2.0] - 2026-06-21

[1.2.0]: https://github.com/ndestates/orchestrator/compare/v1.1.0...v1.2.0

### Added

- **docker-expert** — hardened multi-stage production images, mandatory `.dockerignore`, thin runtime; chains `docker-deploy` and expanded `deploy-check`
- **Database & framework experts** — `mariadb-database-expert`, `sqlite-database-expert`, `data-architect-expert`, `vector-database-expert` (fit assessment), `nextjs-expert`, `astro-expert`, `nuxt-expert`, `go-expert`
- **Chains** — `laravel-database-design`, `database-design`, `vector-db-assess`, `vector-db-setup`, `deploy-dns-infra`; framework routing in `web-design`

### Changed

- **aws-route53-dns** — production deploy DNS package (SES DKIM/SPF/DMARC/MX), pre-go-live checklist, DO Cloud Firewall handoff
- **github-workflow-expert** — integrates docker-expert in deploy-check and docker-deploy chains
- **digitalocean-app-platform-docr-deploy** — docker-expert + Route 53 coordination for go-live

## [1.1.0] - 2026-06-20

[1.1.0]: https://github.com/ndestates/orchestrator/compare/v1.0.1...v1.1.0

### Added

- **github-workflow-expert** — programmatic GitHub Actions workflow CRUD and secrets management; synced to Claude/Copilot; chains `github-workflow-setup` and `deploy-check`
- **Weekly L1 watch loops** — `cache-freshness-watch`, `chain-health-watch`, `github-ci-watch` (patterns, host scripts, `loop-weekly-watch.yml`, chain registry entries)
- **push-secrets-guard** — `scripts/git-push-secrets-guard.py` blocks live `.env` files, dated `backup/20*.sql.gz`, flare incident logs, and common secret patterns before commit/push; wired into `.githooks/pre-commit` + `pre-push`, `git-workflow-guardrails`, `push-secrets-guard` chain, and optional CI job patcher
- **wave-apps.sh** — helper for subset wave scripts to read full inventory

### Changed

- **digitalocean-app-platform-docr-deploy** skill refreshed as Senior DevOps expert with `git-workflow-guardrails` and `github-expert` integration
- **Template deploy bundle** — includes weekly loop workflow and host scripts; subset wave deploy/commit scripts use `wave-apps.sh`
- **Wave inventory** — `project` app renamed to `ndestates-io`; stack profile aliases updated

### Infrastructure

- EOD session housekeeping: TODO carry-forward, changelog scaffold, `.gitignore` hygiene (PR #45)
