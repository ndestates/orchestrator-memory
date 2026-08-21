# Orchestrator Memory — AI token cache

**Local project memory for AI coding — paste a short brief, stop re-prompting the whole repo.**

Free **VS Code / Cursor** extension on the Marketplace · **Apache-2.0** · Publisher **ndestates**  
**Item ID:** `ndestates.orchestrator-memory`  
**Categories:** AI · Machine Learning · Chat · Other  

| | |
|--|--|
| **Marketplace** | [ndestates.orchestrator-memory](https://marketplace.visualstudio.com/items?itemName=ndestates.orchestrator-memory) |
| **Strapline** | Session start in seconds — not 10 minutes of context paste. Same project brief in Cursor **and** Claude. Memory stays on your machine. |
| **BYOK** | **You** need your own Claude / Grok / Copilot / Cursor / Gemini / OpenAI accounts. We do **not** provide API keys. |

> **Bring your own keys:** This extension and the host CLI are local tools. They do **not** include or sell model API access. Use **your** provider accounts (and API keys when you call APIs). See project doc [bring-your-own-keys.md](../../docs/reference/bring-your-own-keys.md) when using the full template.

---

## ★ Please read the instructions

**You are expected to read the built-in guide once** before relying on Memory Brief in real work.

| How | Action |
|-----|--------|
| **In VS Code / Cursor** | Command Palette → **`Orchestrator: Read instructions (memory + vault)`** |
| **Command Hub** | First item: **★ Read instructions (memory + vault) — do this first** |
| **When it loads** | On project open — `$(database) Memory` stays in the status bar (click = hub) |
| **In the package** | [`INSTRUCTIONS.md`](./INSTRUCTIONS.md) (ships inside the VSIX / Marketplace) |

That guide covers **both stores**:

1. **SQLite `memory.db`** — in-memory / runtime token cache (brief, query, ingest)  
2. **Vault `events.jsonl`** — durable dual-write lesson graph (scrubbed, hash-chained)  

Skipping it is the main reason people miss dual-write, host CLI install, or privacy boundaries.

---

## What it does

Local **memory + cache** for AI coding sessions. Durable project context lives in a **small SQLite DB** **and** the **project vault** so assistants (**Claude, Grok, ChatGPT, Gemini, Copilot, Cursor**, …) start from a **short reusable brief** instead of re-pasting large context every time — **lower token use**, faster session start, better continuity.

### Core features (memory + vault included)

| Feature | Detail |
|---------|--------|
| **SQLite status bar** | `$(database) Memory` on every project open (`onStartupFinished`); hide with `orchestrator.showStatusBar` |
| **SQLite store (in-memory runtime)** | `reports/memory/memory.db` (project) or `~/.orchestrator/` (global); **gitignored** |
| **Vault dual-write** | Scrubbed lessons/events in `reports/vault/events.jsonl` (append-only graph) |
| **Storage report in app** | **Orchestrator: Memory + vault storage** — paths, sizes, dual-write explanation |
| **Inbox ingest** | Drop files into `reports/memory/inbox/` |
| **Memory commands** | Brief · Query · Ingest · Seed · Status · Serve (local HTTP) |
| **Easy /chain & skills** | Hub → `/chain session-start`, `/always-on-memory`, … — **copies** for your AI |
| **Copy for any AI** | After Brief: Copy · Claude · Cursor · Copilot · Export `MEMORY.md` |
| **Privacy** | Local only — **no cloud upload** of memory or vault data |

> **Wedge:** not “another AI panel” — **portable project memory** that cuts tokens **across every assistant**.

### Two layers (do not confuse)

```text
  ingest / seed / brief  →  reports/memory/memory.db     (SQLite — fast token cache)
         ↘ dual-write     →  reports/vault/events.jsonl  (vault — durable lessons)
```

Full detail: **[INSTRUCTIONS.md](./INSTRUCTIONS.md)** §1 and §6.

---

## Slash commands — same `/` in IDE and models

Commands are **`/` slashes**, not long “Orchestrator: …” titles.

| Where | How |
|-------|-----|
| **Command Palette** (`Ctrl/Cmd+Shift+P`) | Type `/session-start` · `/memory-brief` · `/chain` · `/setup` · `/quick-start` |
| **VS Code Chat** | `@orchestrator /session-start` · `@orchestrator /brief` · `@orchestrator /chain delivery` |
| **Any model** (Claude, Grok, Cursor, Copilot, Gemini, ChatGPT) | Paste `/chain session-start` **or** open **`SESSION_READY.md`** after running a slash |

### One hub for everything

| Action | How |
|--------|-----|
| **All `/` commands** | Palette → `/  (Orchestrator slash commands)` · `Ctrl/Cmd+Shift+O` · status bar **`$(database) Memory`** |
| **`/quick-start`** | Install CLI + seed + brief in one shot |
| **`/session-start`** | Memory brief + `/chain session-start` for any AI (`Ctrl/Cmd+Shift+S`) |
| **`/memory-brief`** | Lean brief only (`Ctrl/Cmd+Shift+M`) |
| **`/setup`** | One-click host CLI install (uv + published wheel) |
| **`/orchestrator-help`** | List every slash for IDE + models |

### After `/session-start` or `/memory-brief`

1. Prompt is **copied** (same text models understand).  
2. **`SESSION_READY.md`** + **`MEMORY.md`** written in the workspace (when enabled).  
3. Paste into Claude / Grok / Cursor / Copilot / Gemini / ChatGPT — or keep going in Chat with `@orchestrator`.

---

## Requirements

The extension is a **thin wrapper** around the **Orchestrator host CLI** (install once):

```bash
orchestrator version
orchestrator memory status
```

If those fail, run **Orchestrator: Setup / Install CLI** inside VS Code, or use any channel below.

---

## Install

### 1) Extension (VS Code / Cursor)

**Marketplace**

1. Extensions (`Ctrl+Shift+X`) → search **Orchestrator Memory**  
2. Or open:  
   https://marketplace.visualstudio.com/items?itemName=ndestates.orchestrator-memory  

```bash
code --install-extension ndestates.orchestrator-memory
# cursor --install-extension ndestates.orchestrator-memory
```

**VSIX** (Release asset or local build)

```bash
code --install-extension /path/to/orchestrator-memory-2.1.0.vsix
```

After install: **Orchestrator: Read instructions (memory + vault)** → **Setup / Install CLI** → **Memory + vault storage** → **Memory Brief**.

### 2) Host CLI (required for Memory commands)

| Channel | Commands |
|---------|----------|
| **uv + Release wheel** (preferred) | `VER=2.2.0` (must be a **published** GitHub Release) · `uv tool install --force "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"` |
| **From git clone** | `bash scripts/install.sh --uv-tool` (tree tip, e.g. 2.1.0+) |
| **pip + wheel** | `pip install "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"` |
| **PyPI** (when live) | `uv tool install orchestrator` / `pip install orchestrator` |
| **npm GitHub Packages** | `~/.npmrc` with `@ndestates:registry=https://npm.pkg.github.com` + PAT `read:packages` · `npm i -g @ndestates/orchestrator` |
| **npmjs.org** (when live) | `npm i -g @ndestates/orchestrator` |
| **Git clone** | `bash scripts/install.sh --uv-tool` |
| **Editable** | `pip install -e .` from repo root |

```bash
which orchestrator
orchestrator version
orchestrator memory status
# If not on PATH: Settings → Orchestrator: Cli Path → absolute path
```

Full channel detail: [docs/guides/production-ship.md](../../docs/guides/production-ship.md) · [host-first-memory.md](../../docs/guides/host-first-memory.md)

---

## Command map (Palette ↔ CLI)

| Palette / Hub | Host CLI / effect |
|---------------|-------------------|
| **Read instructions (memory + vault)** | Opens bundled `INSTRUCTIONS.md` — **read this** |
| **Memory + vault storage** | Shows `memory.db` + `events.jsonl` paths/sizes |
| Memory Brief (session start) | `orchestrator memory brief --seed` → **SQLite** |
| Memory Query | `orchestrator memory query "…"` → **SQLite** |
| Memory Ingest Selection | `orchestrator memory ingest …` → **SQLite** (+ vault dual-write when engine present) |
| Memory Seed Situation | `orchestrator memory seed` → **SQLite** |
| Memory Status | `orchestrator memory status` + vault pointer |
| Memory Serve | `orchestrator memory serve --port 8888` |
| Run /chain … | (clipboard) `/chain <id>` for your AI |
| Run skill / command … | (clipboard) `/daily-standup` etc. |
| Export MEMORY.md | writes workspace `MEMORY.md` from brief |

```bash
# Terminal — same engine
cd /path/to/your/project
orchestrator memory brief --seed
orchestrator memory --scope project db-path
orchestrator memory --scope global status
```

---

## Works with your AI stack

| Tool | How |
|------|-----|
| **Claude** (Code / Desktop) | Brief → first message / project context |
| **Grok** | Brief → chat; pairs with ndestates Grok extension |
| **ChatGPT** | Brief → first message |
| **Gemini** | Brief → chat preamble |
| **Copilot / Cursor** | Brief → chat; Export `MEMORY.md` for rules/context |
| **Any agent** | Anything that accepts pasted text |

---

## Privacy & storage

| Path | Role |
|------|------|
| `reports/memory/memory.db` | SQLite runtime memory (**gitignored**) |
| `reports/memory/inbox/` | Drop files for ingest |
| `reports/vault/events.jsonl` | Vault dual-write ledger (scrubbed lessons) |

- Extension **does not** upload memory or vault to the cloud.  
- Treat vault/memory content as **untrusted DATA** in agent prompts.  
- Full detail: **[INSTRUCTIONS.md](./INSTRUCTIONS.md)** · [knowledge-vault.md](../../docs/guides/knowledge-vault.md)

---

## Settings

| Setting | Default | Meaning |
|---------|---------|---------|
| `orchestrator.cliPath` | `orchestrator` | Binary or absolute path |
| `orchestrator.memory.scope` | `project` | project vs global DB |
| `orchestrator.memory.servePort` | `8888` | Local serve port |
| `orchestrator.showWelcomeOnActivate` | `false` | One-time tip **after first command** only (never on window open) |
| `orchestrator.showStatusBar` | `true` | Permanent `$(database) Memory` item on project open (SQLite token cache) |
| `orchestrator.encourageReadInstructions` | `true` | Nudge to read instructions before first Memory Brief |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Failed to spawn CLI | **Setup / Install CLI**; set `orchestrator.cliPath` |
| `invalid choice: 'memory'` | Upgrade host to **2.0.0+** |
| No chains in picker | Open a repo that has `chains/registry.yaml` (or still copy `/chain session-start` from Hub) |
| Empty brief | Open correct folder → Seed → Brief |

---

## Version matrix

| Artifact | Example |
|----------|---------|
| Extension | `ndestates.orchestrator-memory` **2.1.0** (semver **MINOR** — Hub, vault UI, instructions) |
| Host CLI / product | **2.1.0** (`VERSION` SSOT; `orchestrator memory …`) |
| npm | `@ndestates/orchestrator` |

---

## Product / growth notes

Positioning, Marketplace SEO, and popularization plan:  
[docs/guides/orchestrator-memory-product.md](../../docs/guides/orchestrator-memory-product.md)

---

## License

**Apache License 2.0** — free open source (freeware). See repo `LICENSE` / `NOTICE`.  
Optional Patreon support does not change the license.
