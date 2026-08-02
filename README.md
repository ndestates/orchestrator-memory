# Orchestrator Template

Project-agnostic AI orchestration template for manifest-first, cache-first development. Ships skills, prompts, agents, loops, and chains — for **Grok, Claude Code, GitHub Copilot, Gemini, Cursor, and ChatGPT/OpenAI**.

**License:** [Apache-2.0](LICENSE) — **freeware open source** (no paid tier required)  
**Support (optional):** [Patreon](https://www.patreon.com/ndestates) — donate if you like; **not** a license key  
**Repository:** [ndestates/orchestrator](https://github.com/ndestates/orchestrator) · **Latest:** see [Releases](https://github.com/ndestates/orchestrator/releases)

**Production install (npm / pip / VS Code):** [docs/guides/production-ship.md](docs/guides/production-ship.md)

**Full documentation:** [docs/index.md](docs/index.md) (GitHub Docs style hub; agent cache in docs/codebase/).

## Quick start

**Docs:** [Installation](docs/getting-started/installation.md) · [Multi-platform MCP + host tools](docs/guides/multi-platform-mcp-and-host-tools.md) · [WebMCP (beta)](docs/guides/webmcp-beta.md) · [Per-app upgrade](docs/guides/per-app-upgrade.md) · [Platform surfaces](docs/reference/platform-surfaces.md) · [Licensing](docs/reference/licensing.md) · [docs hub](docs/index.md)

```bash
# Linux / macOS / WSL — bootstrap + CLI + ripgrep + MCP venv
bash scripts/install.sh --cli --host-tools --mcp

# Windows PowerShell
# .\scripts\install.ps1 -Cli -HostTools

# Per-app install (one repository; not multi-app wave)
orchestrator init /path/to/app --no-pr --dry-run
orchestrator init /path/to/app --no-pr

# After a release (stable example):
# orchestrator upgrade /path/to/app --from-github v1.8.9 --yes --no-pr
# Optional multi-workstream pre-release (opt-in; not Latest):
# orchestrator upgrade /path/to/app --from-github v1.9.1 --yes --no-pr
```

Fleet wave deploy to multiple apps is **disabled by default**. Use per-app `init` / `upgrade` only.

Then in your AI session:

| Command | When |
|---------|------|
| `/chain session-start` | Default session opener (vault + lean wiki brief) |
| `orchestrator memory brief --seed` | Host-first always-on memory (any project) |
| `/multi-workstream list` | Day-scale tracks (diamond · serial · worktree · prompts · guard) |
| `/chain wiki-query` | Ask the compounding wiki |
| `/chain wiki-ingest` | Ingest one `raw/` source into `wiki/` |
| `bash scripts/setup-who-i-am.sh` | One-time operator profile (then edit `.grok/memories/who-i-am.md`) |
| `/load-project-cache-first` | Master cache loader |
| `/orchestrator <task>` | Multi-step planning |
| `/chain eod-shutdown` | End of day (alias: `/chain end-of-session`) |
| `/ddev-cleanup` | EOD cleanup step (also last step of eod-shutdown chain) |

## Architecture

| Layer | Registry | Purpose |
|-------|----------|---------|
| **Manifest** | `.github/project-manifest.yaml` (canonical); `.grok/project-manifest.yaml` preferred for Grok | Stack, paths, token/loop/chain/**wiki** policy |
| **Cache** | `docs/codebase/` | Lean code context for every session |
| **LLM Wiki** | `wiki/` + `raw/` + `/llm-wiki` | Compounding multi-source knowledge (Karpathy pattern) — [guide](docs/guides/llm-wiki.md) |
| **Vault** | `reports/vault/events.jsonl` | Hash-chained lessons / integrity graph |
| **Chains** | `CHAIN.md`, `chains/registry.yaml` | On-demand skill composition (`/chain`) |
| **Loops** | `LOOP.md`, `STATE.md` | Scheduled L1 triage + weekly watches |
| **Sync** | `scripts/sync_grok_to_github_claude.py` | `.grok/` → `.github/` + `.claude/` |

**Grok on app repos:** Discovery prefers `.grok/project-manifest.yaml` when present (see `_engine/manifest_sync.py` and cache/scan scripts). Install or update each app with the CLI — not fleet wave.

**Branch promotion:** `feature/*` → `develop` → `master` (automated draft PRs via `branch-promotion-prs.yml`).

## Key directories

```
.grok/            # Grok Build (skills + config.toml MCP)
.github/          # Copilot skills + canonical project-manifest
.claude/          # Claude Code commands/agents + MCP example
.gemini/          # Gemini prompts/instructions + MCP example
.cursor/          # Cursor rules + mcp.json
.chatgpt/         # ChatGPT / Codex / OpenAI Agents surface + MCP examples
mcp-server/       # Enterprise MCP package + multi-host client configs
TODO/             # Daily task files (YYYY-MM-DD_TODO.md)
reports/loops/    # L1 triage artifacts
chains/           # Machine-readable chain catalog
```

**Host tools:** `scripts/install-host-tools.sh` (ripgrep) · **MCP:** `scripts/ensure-mcp-host.sh` (auto-repaired on session-start).

## Active chains

See [CHAIN.md](CHAIN.md). Includes `session-start`, `eod-shutdown`, `research-deep-dive`, `delivery`, `repo-health`, `complex-task`, and more.

## CI

- `chain-audit.yml` — validates `chains/registry.yaml`
- `loop-daily-triage.yml` — weekday L1 host snapshot
- `loop-weekly-watch.yml` — Monday L1 watches (cache, chain, CI, repo health)
- `run-chain.yml` — one-click `workflow_dispatch` chain trigger
- `branch-promotion-prs.yml` — promotion PR automation
- `mcp-security.yml` — MCP server tests + threat scan on `mcp-server/**`
- `tooling-tests.yml` — root pytest harness (`tests/`) for the deploy/customize/scan/sync tooling

## Versioning

The template version is the single source of truth in [`VERSION`](VERSION) (semver),
mirrored into the wheel and git release tags. Host CLI (`orchestrator`) supports
`version`, `status`, `memory`, `init`, `upgrade`, `self-upgrade`, and more.

**Per-app only:** Fleet wave deploy is **permanently removed**. Install or upgrade
each app with `orchestrator init` / `orchestrator upgrade`.

**License:** Apache-2.0 freeware. Optional license-server code is for advanced/self-host
gates only — **not** required for public use. See [Licensing](docs/reference/licensing.md).

## Tooling

```bash
python3 scripts/sync_grok_to_github_claude.py   # after .grok/ edits
bash scripts/chain-audit.sh
bash scripts/loop-audit.sh
bash scripts/sync-all-projects.sh               # reconcile all ~/projects with remotes
PYTHONPATH=src:scripts pytest tests -q          # tooling + CLI test harness
orchestrator init /path/to/project --no-pr --selections grok,chains
orchestrator memory brief --seed
orchestrator status /path/to/project --json
# optional advanced only:
# orchestrator license
# orchestrator license-server

# Multi-AI best practices (Claude research rolled out)
See reports/research/multi-ai-best-practices-rollout-plan.md and the "who I am" + thinking partner techniques adapted for Grok / Claude / Copilot / Gemini (.gemini/ support added). Includes chain engineering improvements for tool use and realistic step limits.

## Tools across platforms
- Primary: MCP server for tool calling (cache, state, audits, readonly scripts).
- Configs and examples for Grok, Cursor/Gemini, Claude.
- Function calling schemas for Gemini API.
- See `docs/reference/tools/multi-platform-tool-use.md` and `mcp-server/README.md`.
- Deploy with mcp selection.
```

## Documentation

**[docs/index.md](docs/index.md)** — navigable documentation (getting started, guides, reference, operations).

| Doc | Contents |
|-----|----------|
| [docs/index.md](docs/index.md) | Human documentation hub |
| [docs/codebase/README.md](docs/codebase/README.md) | Agent cache index |
| [INSTALL.md](INSTALL.md) | Short install pointer → full installation + licensing docs |
| [Installation](docs/getting-started/installation.md) | Bash, PowerShell, pip, npm, per-app CLI |
| [Per-app upgrade](docs/guides/per-app-upgrade.md) | After each release — upgrade apps one-by-one (no wave) |
| [Licensing](docs/reference/licensing.md) | License gate configuration and verify steps |
| [CLAUDE.md](CLAUDE.md) | Claude Code instructions |
| [.grok/README.md](.grok/README.md) | Grok command index |

## Adopting this template

See [docs/TEMPLATE_ADOPTION.md](docs/TEMPLATE_ADOPTION.md) (if present) or [INSTALL.md](INSTALL.md).