# Changelog

This extension follows [Semantic Versioning](https://semver.org/):

| Bump | When |
|------|------|
| **MAJOR** | Breaking change to command IDs, settings, or required host CLI contract |
| **MINOR** | Backward-compatible features (new commands, Hub, storage UI, docs product surface) |
| **PATCH** | Fixes, copy, icon, metadata only |

Host product version lives in repo root `VERSION` and **must match** the release train
(CLI wheel + extension + Marketplace). Bump via root `VERSION` + `node scripts/npm/sync-version.js`.

## 3.0.0 — 2026-09-17

**SemVer: MAJOR** — product line moves to **3.x**. Public install docs and metadata point at `ndestates/orchestrator-memory`. npm and the GitHub Release wheel must ship the same `X.Y.Z`.

### Changed

- Align extension + `publishedCliVersion` with root **VERSION 3.0.0**
- Repository / bugs URLs → public `orchestrator-memory`
- Host CLI install copy: npm-only for users

## 2.3.0 — 2026-08-16

**SemVer: MINOR** — product version lockstep with template **2.3.0** (self-regulating skills).

### Changed

- Align extension + `publishedCliVersion` with root **VERSION 2.3.0**
- **SQLite status bar** — `$(database) Memory` is visible as soon as a project window opens (`onStartupFinished`); click opens the hub. Restore of the 2.1.0 icon (2.2.1 had hidden it until a command).

## 2.2.5 — 2026-08-15

**SemVer: PATCH** — product version lockstep with template **2.2.5** (skills.sh complement skills).

### Changed

- Align extension + `publishedCliVersion` with root **VERSION 2.2.5**

## 2.2.3 — 2026-08-04

**SemVer: PATCH** — product copy + version lockstep (CLI = extension = Marketplace next).

### Changed

- Align extension + `publishedCliVersion` with root **VERSION 2.2.3**
- Product README / npm package metadata improved for Marketplace and GitHub discoverability (root README + package.json)

## 2.2.2 — 2026-08-04

**SemVer: PATCH** — product version lockstep (CLI = extension = Marketplace next).

### Changed

- Align extension + `publishedCliVersion` with root **VERSION 2.2.2** (marketplace already has **2.2.1**; next ship must be higher)
- Session-start: active-project-only security sweep; remote_last hard rules (no bot tips)

## 2.2.1 — 2026-08-02

**SemVer: PATCH** — activation UX.

### Changed

- **No startup activation** — does not run when a window opens  
- Activates only on **Command Palette / keybinding / context menu** or **Chat** `@orchestrator`  
- Welcome popup **off by default** (`showWelcomeOnActivate: false`)  
- Status bar appears only after activation (optional setting `showStatusBar`)

## 2.2.0 — 2026-08-02

**SemVer: MINOR** — slash commands are first-class in the IDE and in models.

**Canonical for Grok + Claude:** type **`/chain session-start`** on the agent command line (unchanged). Extension helpers prepare the same slash; they do not replace it.

### Added

- **Slash commands in Command Palette** — type `/session-start`, `/memory-brief`, `/chain`, `/setup`, … (category Orchestrator)
- **VS Code Chat participant** `@orchestrator` with the same slashes:
  - `@orchestrator /session-start`
  - `@orchestrator /brief`
  - `@orchestrator /chain session-start`
  - `@orchestrator /query …`
  - `@orchestrator /setup`
  - `@orchestrator /help`
- **Same `/` text for models** — Claude, Grok, Cursor, Copilot, Gemini, ChatGPT: paste `/chain session-start` or open `SESSION_READY.md`
- **`/quick-start`** — one-shot: install host CLI (uv) + memory dirs + seed + brief
- **One-click `/setup`** — runs `uv tool install` against the published GitHub Release wheel (setting `orchestrator.publishedCliVersion`, default **2.0.0**)
- Writes **`SESSION_READY.md`** + **`MEMORY.md`** so any model can read the prepared `/` command
- Status bar: `/session-start` · Hub: list of all `/` commands
- Keybinding: `Ctrl/Cmd+Shift+S` → `/session-start`

### Changed

- Welcome flow offers `/quick-start` / `/session-start` instead of forcing a long README first
- `encourageReadInstructions` default **false** (easier first run)
- Engines: VS Code **^1.90.0** (Chat participants)

### Install note

Host CLI must be **2.0.0+** (`orchestrator memory …`). Published wheel on GitHub: **v2.2.0** (this release). Host CLI **2.0.0+** required for memory.

## 2.1.0 — 2026-08-01

**SemVer: MINOR** (significant feature release after 2.0.x packaging).

### Added

- **Command Hub** (`Ctrl/Cmd+Shift+O`, status bar) — memory · `/chain` · skills · setup · docs  
- **Run /chain …** and **Run skill / command …** (clipboard prompts for Claude / Grok / Cursor / Copilot)  
- **Copy brief** for Claude / Cursor / Copilot · **Export MEMORY.md**  
- **Setup / Install CLI** wizard (uv/pip one-liners)  
- **INSTRUCTIONS.md** (bundled) — SQLite `memory.db` + vault `events.jsonl` dual-write, all install channels  
- **Read instructions (memory + vault)** — first-run auto-open; encourage-read before first Brief  
- **Memory + vault storage** — paths, sizes, dual-write report  
- Marketplace straplines / SEO keywords for token-cache positioning  
- Keybindings: Hub, Memory Brief; context menu ingest  

### Changed

- Display name / description: *AI token cache* · local project memory one-liner  
- Status / ingest messaging includes vault dual-write  
- Docs SSOT: `INSTRUCTIONS.md` + README multi-channel install  

### Notes on interim numbers

Local builds briefly used **2.0.11–2.0.13** while iterating Marketplace/icon/copy. Those are **superseded** by **2.1.0** for any public tag/release (do not publish 2.0.11–2.0.13 as separate semver history on Marketplace if avoidable; ship **2.1.0**).

## 2.0.1

- Marketplace-ready package (icon, metadata)  
- Align publish flow with vscode-grok4  

## 2.0.0

- Initial public release: brief / query / ingest / seed / status / serve  
