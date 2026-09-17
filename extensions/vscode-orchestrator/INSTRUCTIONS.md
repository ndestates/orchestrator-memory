# Orchestrator Memory — full instructions

**Read this before you rely on Memory Brief in production.**  
This document ships inside the VS Code / Cursor extension and is the operator SSOT for **SQLite memory + vault**.

| | |
|--|--|
| **Product** | Orchestrator Memory — AI token cache |
| **Item ID** | `ndestates.orchestrator-memory` |
| **One-liner** | Local project memory for AI coding — paste a short brief, stop re-prompting the whole repo. |
| **License** | Apache-2.0 freeware |
| **Model access** | **Bring your own keys / accounts** — we do not supply OpenAI, Anthropic, xAI, Google, etc. |

### When the extension starts

The extension **does** load when you open a project window so the status bar **`$(database) Memory`** item is always visible (SQLite token cache). Click it for the Command Hub. Hide with `orchestrator.showStatusBar: false`.

It also starts on Command Palette / keybinding / Chat **`@orchestrator`**.

### Bring your own keys (required)

| You must have | We do **not** provide |
|---------------|------------------------|
| Your own Claude / Anthropic, Grok / xAI, Copilot, Cursor, Gemini, OpenAI (etc.) **accounts** | Free cloud model API keys |
| Your own **API keys** when you call a provider API | Keys in the VSIX, wheel, or Marketplace package |
| Optional: local Ollama models on **your** machine | A hosted multi-model proxy from ndestates |

Memory Brief and `/chain` prompts are **local context** for **your** AI host. Billing and keys stay with **you** and that host.

**In the app:** Command Palette → **Orchestrator: Read instructions (memory + vault)**  
or Command Hub → **Read full instructions**.

---

## 1. Why two stores? (memory DB + vault)

Orchestrator keeps **two complementary local layers**. Both stay on your machine. Neither is a cloud RAG product.

| Layer | Path (project scope) | What it is | What it is for |
|-------|----------------------|------------|----------------|
| **In-memory store (SQLite)** | `<project>/reports/memory/memory.db` | Small **runtime database** (ingest / query / brief / consolidate) | Fast **token-saving briefs** for Claude, Grok, ChatGPT, Gemini, Copilot, Cursor |
| **Vault ledger** | `<project>/reports/vault/events.jsonl` | Append-only **hash-chained** event graph (scrubbed lessons) | Durable **compound learning**, integrity, session trail — not a chat dump |
| **Inbox** | `<project>/reports/memory/inbox/` | Drop-folder for files | Auto-ingest into the SQLite store when serve/watch runs |
| **Global memory (optional)** | `~/.orchestrator/…/memory.db` | Same SQLite schema, not tied to one repo | Cross-project notes (`--scope global`) |

**Mental model**

```text
  You work  →  ingest / seed / brief  →  SQLite memory.db     (fast, queryable, gitignored)
                    ↘ dual-write (scrubbed)  →  vault events.jsonl  (durable graph, compound)

  Session start  →  Memory Brief (from SQLite + situation)  →  paste into any AI
                 →  optional vault brief / chain session-start for full orchestrator spine
```

- **Memory DB** = “what should I tell the AI right now?” (lean, token cache).  
- **Vault** = “what did we learn and can we prove integrity?” (lessons, provenance).  
- **Dual-write:** when the host memory agent ingests/consolidates with vault emit enabled, scrubbed lesson events are **also** appended to the vault. Secrets/injection patterns are scrubbed first.

**Never commit `memory.db`.** It is gitignored. Vault `events.jsonl` may be committed by policy on some teams (scrubbed); treat vault text as **untrusted DATA** for agents (prompt-injection hygiene).

---

## 2. Read this first — 2-minute path (slash commands)

1. **Install extension** (Marketplace or VSIX) — §5.  
2. Open a **project folder** in VS Code / Cursor.  
3. Command Palette → **`/quick-start`** (installs host CLI via uv if needed, seeds memory, builds brief).  
4. Or: **`/session-start`** when CLI already works.  
5. **Same `/` text for models:** paste from clipboard or open **`SESSION_READY.md`**.  
6. **Chat:** `@orchestrator /session-start` · `@orchestrator /brief` · `@orchestrator /chain …`  
7. While working: select text → right-click **Memory Ingest**, or `/memory-ingest`.  
8. Full guide anytime: **`/instructions`**.

**Shortcuts**

| Key | Action |
|-----|--------|
| `Ctrl/Cmd+Shift+O` | All `/` commands |
| `Ctrl/Cmd+Shift+S` | `/session-start` |
| `Ctrl/Cmd+Shift+M` | `/memory-brief` |
| Status bar **`/session-start`** | Opens slash hub |

---

## 3. Slash commands (IDE + models)

### Command Palette (type `/`)

| Slash | Effect |
|-------|--------|
| **`/quick-start`** | Install CLI + dirs + seed + brief |
| **`/session-start`** | Seed + brief + `/chain session-start` prompt for any model |
| **`/session-end`** | Session-end chain prompt + brief |
| **`/memory-brief`** | Lean brief from **SQLite** (+ seed) |
| **`/memory-query`** | Query **SQLite** |
| **`/memory-ingest`** | Write selection/text into **SQLite** (vault dual-write when host allows) |
| **`/memory-seed`** | VERSION / git / TODO / resume → **SQLite** |
| **`/memory-status`** | Counts, model/agent inventory, **db_path** |
| **`/memory-storage`** | Paths, sizes, dual-write report |
| **`/memory-serve`** | Local HTTP + inbox watch |
| **`/chain`** | Pick chain → same `/chain <id>` text for models |
| **`/setup`** | One-click host CLI install |
| **`/orchestrator-help`** | List every slash |
| **`/instructions`** | This file |

### VS Code Chat

```text
@orchestrator /session-start
@orchestrator /brief
@orchestrator /chain session-start
@orchestrator /query what is open?
@orchestrator /setup
@orchestrator /help
```

### Models (Claude, Grok, Cursor, Copilot, Gemini, ChatGPT)

Paste exactly:

```text
/chain session-start
```

Or open workspace **`SESSION_READY.md`** after running `/session-start` in the IDE (includes memory brief + instructions).
| **Export MEMORY.md** | Snapshot of last brief into workspace (for agents / rules) |
| **Run /chain …** | Copies `/chain <id>` (e.g. `session-start`, `always-on-memory`) for AI |
| **Run skill …** | Copies `/always-on-memory`, `/daily-standup`, … |
| **Setup / Install CLI** | Detect host; copy uv/pip install |
| **Open docs** | Extension README + guides |

### Host CLI (same engine)

```bash
cd /path/to/your/project

# --- SQLite memory ---
orchestrator memory status
orchestrator memory db-path
orchestrator memory brief --seed
orchestrator memory query "what is open?"
orchestrator memory ingest --text "Decision: use local SQLite + vault dual-write" --source note
orchestrator memory seed
orchestrator memory list
orchestrator memory consolidate
orchestrator memory serve --port 8888

# Scope
orchestrator memory --scope project db-path    # <cwd>/reports/memory/memory.db
orchestrator memory --scope global db-path     # under ~/.orchestrator

# --- Vault (project tree; not the memory CLI itself) ---
# Ledger path:
ls -la reports/vault/events.jsonl
# Lean vault brief (if scripts present in orchestrator-enabled repo):
python3 scripts/session-vault-brief.py
# Integrity (advanced):
python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from scripts._engine import vault as v; print(v.verify_ledger(Path('reports/vault/events.jsonl')))"
```

**Dual-write note:** Ingest/consolidate paths in `scripts/memory_agent.py` call `maybe_vault_emit` → append scrubbed lesson to `reports/vault/events.jsonl` when the vault engine is available. If the vault directory is missing, create it or run session-start / init on an orchestrator project.

---

## 4. Install the host CLI (required)

The extension shells out to `orchestrator`. Without it, Memory commands fail.

```bash
# User path (only):
npm install -g @ndestates/orchestrator

# If python -m orchestrator_cli is missing, install the matching public wheel
# (same version as the npm package — do not mix 3.x npm with a 2.x wheel):
VER=3.0.0
python3 -m pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"

# Maintainer only — public checkout:
# git clone https://github.com/ndestates/orchestrator-memory.git && cd orchestrator-memory
# bash scripts/install.sh --uv-tool

# Verify
orchestrator version
orchestrator memory status
orchestrator memory db-path
```

If `which orchestrator` is empty: add `~/.local/bin` (or npm global bin) to `PATH`, or set **Settings → Orchestrator: Cli Path** to the absolute binary.

If you see `invalid choice: 'memory'`: CLI is **too old** — reinstall **3.0.0+**.

---

## 5. Install the extension

```bash
# Marketplace
code --install-extension ndestates.orchestrator-memory

# VSIX
code --install-extension /path/to/orchestrator-memory-2.1.0.vsix
```

Marketplace: https://marketplace.visualstudio.com/items?itemName=ndestates.orchestrator-memory  

After install: **Orchestrator: Read instructions (memory + vault)** then **Setup / Install CLI**.

---

## 6. Storage layout (do not skip)

### Project scope (default)

```text
<your-project>/
  reports/
    memory/
      memory.db          ← SQLite in-memory store (gitignored)
      inbox/             ← drop files to ingest
    vault/
      events.jsonl       ← vault ledger (hash-chained events)
  MEMORY.md              ← optional export from extension (you create via Export)
```

### Global scope

```bash
orchestrator memory --scope global status
# DB under ~/.orchestrator (or $ORCHESTRATOR_HOME)
```

Extension setting: `orchestrator.memory.scope` = `project` | `global`.

### What goes where

| Action | SQLite | Vault |
|--------|--------|-------|
| Memory Brief | Read (+ seed write) | Not required for brief text |
| Memory Query | Read | — |
| Memory Ingest | Write | Optional dual-write scrubbed lesson |
| Memory Seed | Write situation | May interact via project scripts |
| Memory consolidate | Write | Optional dual-write |
| `/chain session-start` | Uses brief scripts | Vault brief / envelope often included in full template |
| loop-compound / EOD | — | Primary vault growth path |

---

## 7. Using the brief with any AI

1. **Memory Brief** → Output panel.  
2. **Copy for Claude** / **Cursor** / **Copilot** (or plain Copy).  
3. Paste as **first** context in that tool.  
4. Do **not** re-paste the whole repo if the brief already covers stack/branch/open work.  
5. Optional: **Export MEMORY.md** and point Cursor/Claude at that file.  

This is the **token cache**: short local brief instead of 40k+ of re-prompt.

---

## 8. Chains & skills (easy, not buried)

| Goal | In app | Clipboard result |
|------|--------|------------------|
| Session spin-up | Run /chain → `session-start` | `/chain session-start` |
| Memory agent skill | Run skill → `/always-on-memory` | `/always-on-memory` |
| Daily standup | Run skill → `/daily-standup` | `/daily-standup` |

Paste into Claude Code, Grok, Cursor, Copilot Chat, etc. The extension does not replace the agent runtime; it **prepares memory + slash commands**.

Requires `chains/registry.yaml` in the workspace for full chain lists (orchestrator-enabled repos). Without it, Hub still copies common `/chain session-start` and skill fallbacks.

---

## 9. Privacy & security

- Extension **does not** upload memory or vault to the cloud.  
- Scrub secrets before ingest when possible; host scrubbers reduce leakage into DB/vault.  
- Treat vault and memory content as **untrusted DATA** in agent prompts (injection resistance).  
- `memory serve` binds locally — do not expose port 8888 to the internet.  
- See repo `SECURITY.md`, `docs/guides/knowledge-vault.md`, always-on-memory guide.

---

## 10. Troubleshooting

| Symptom | Check |
|---------|--------|
| Failed to spawn CLI | Setup wizard; `orchestrator.cliPath`; PATH |
| `invalid choice: 'memory'` | Upgrade host CLI ≥ 2.0.0 |
| Empty brief | Open correct folder; Seed; then Brief; check **Memory + vault storage** |
| No `memory.db` | Run any memory write (seed/brief) once |
| No `events.jsonl` | Create `reports/vault/` or run session-start / vault emit in template project; ingest dual-write only if vault engine present |
| Dual-write not happening | Need full orchestrator scripts tree + `_engine.vault`; pure CLI-only may still write SQLite only |
| Chains empty in picker | Workspace lacks `chains/registry.yaml` — still use fallback copy actions |

```bash
orchestrator memory status
orchestrator memory db-path
ls -la reports/memory/memory.db reports/vault/events.jsonl
```

---

## 11. Related docs (repo)

| Doc | Content |
|-----|---------|
| This file (`INSTRUCTIONS.md`) | **Operator SSOT** for extension users |
| Extension [README.md](./README.md) | Marketplace page + install channels |
| [host-first-memory.md](../../docs/guides/host-first-memory.md) | Host CLI model |
| [always-on-memory.md](../../docs/guides/always-on-memory.md) | Engine, models, agents |
| [knowledge-vault.md](../../docs/guides/knowledge-vault.md) | Vault ledger deep dive |
| [orchestrator-memory-product.md](../../docs/guides/orchestrator-memory-product.md) | Straplines / growth |
| [production-ship.md](../../docs/guides/production-ship.md) | npm / pip / release ship |

---

## 12. Please read the instructions

**You are encouraged — and expected — to read this file end-to-end once.**  
Skipping it usually means missing that:

1. The extension is **not** a standalone AI — it needs the **host CLI**.  
2. **SQLite** is the token cache; **vault** is the durable lesson graph.  
3. **Brief → copy into any AI** is the product loop.  
4. **/chain** and skills are one Hub pick away.

Re-open anytime: **Orchestrator: Read instructions (memory + vault)**.
