# Orchestrator Memory — AI Token Cache for VS Code & Cursor

**Local project memory + AI token cache.**  
Stop re-pasting your entire repo into Claude, Grok, Cursor, Copilot, Gemini or ChatGPT.  
One short, reusable brief → every session. Fewer tokens. Faster start. Real continuity. Everything stays on your machine.

**Free · Apache-2.0 · 100% local · Bring Your Own Keys (BYOK)**

Install (only method): `npm install -g @ndestates/orchestrator`  
https://www.npmjs.com/package/@ndestates/orchestrator

---

## Why AI coding assistants forget (and how this fixes it)

Every new chat starts from zero.  
You re-explain architecture, current branch, decisions, “don’t touch X” rules, and project conventions — burning tokens and killing momentum.

**Orchestrator Memory** is a local AI memory layer and token cache for coding. It stores durable project context in a small SQLite database plus an optional vault dual-write so any assistant (Claude, Grok, Cursor, Copilot, Gemini, ChatGPT, and others) can start from a lean, high-signal brief instead of a wall of context.

Result:
- Dramatically lower token use
- Session start in seconds instead of 10 minutes of pasting
- Better continuity across tools and days
- Privacy by design — no cloud upload of your memory or vault data

---

## Core features

| Feature | What it does |
|---------|--------------|
| **SQLite runtime memory** | Fast project (or global) token cache at `reports/memory/memory.db` (gitignored) |
| **Vault dual-write** | Durable, scrubbed lesson graph in `reports/vault/events.jsonl` |
| **Slash commands everywhere** | `/session-start`, `/memory-brief`, `/chain`, `/quick-start`, `/setup` work in Command Palette, Chat (`@orchestrator`), and any model |
| **One-click brief** | Generates a compact brief, copies it, and writes `SESSION_READY.md` + `MEMORY.md` |
| **Lazy activation** | Zero work on window open — activates only on command, keybinding or Chat |
| **Inbox ingest** | Drop files into `reports/memory/inbox/` for automatic capture |
| **Query / Seed / Status / Serve** | Ask the store, snapshot the situation, inspect health, or run a local HTTP endpoint |
| **Copy targets** | One-click for Claude, Cursor, Copilot or export as `MEMORY.md` |
| **100% local & private** | Memory and vault never leave your machine |

**Wedge:** Not another AI chat panel. Portable project memory that cuts tokens across every assistant you use.

---

## Quick start (under 60 seconds)

1. Install Node.js 18+ and Python 3.10+ if needed.
2. Install once:

```bash
npm install -g @ndestates/orchestrator
orchestrator memory brief --seed
```

3. Optional — write template files in one app:

```bash
npx orchestrator init . --no-pr
```

4. Paste the brief into Claude, Grok, Cursor, Copilot, Gemini or ChatGPT.

Fleet/wave scripts are deleted. Do not use uv, pip, or VSIX to install.

---

## How storage works

```
ingest / seed / brief  →  reports/memory/memory.db     (SQLite — fast token cache)
         ↘ dual-write  →  reports/vault/events.jsonl   (vault — durable lessons)
```

- **SQLite** = runtime memory used for briefs and queries (project-scoped or global).
- **Vault** = append-only, scrubbed event graph for long-term lessons.
- Both stay local. Extension never uploads memory or vault content.

Full details live in the built-in `INSTRUCTIONS.md` (Command Palette → **Orchestrator: Read instructions**).

---

## Commands cheat sheet

| Action | How |
|--------|-----|
| All slash commands | Command Palette → type `/` or `Ctrl/Cmd+Shift+O` |
| Session start (brief + chain) | `/session-start` or `Ctrl/Cmd+Shift+S` |
| Lean brief only | `/memory-brief` or `Ctrl/Cmd+Shift+M` |
| Install host CLI | `/setup` or **Orchestrator: Setup / Install CLI** |
| Quick start (CLI + seed + brief) | `/quick-start` |
| Help | `/orchestrator-help` |
| Chat | `@orchestrator /session-start` |

After a brief you get the text on the clipboard plus optional `SESSION_READY.md` and `MEMORY.md` in the workspace.

---

## Requirements & privacy

- Host CLI: **npx** (preferred) or `orchestrator` on PATH. VSIX/Marketplace is parked.
- **BYOK** — you use your own Claude, Grok, OpenAI, Gemini, Copilot or Cursor accounts. We do not provide, sell or proxy API keys.
- Works with any AI that accepts pasted text.
- Memory and vault data remain on your machine only.

---

## Keywords & discoverability

AI memory · token cache · project memory · local AI · Claude memory · Cursor memory · Copilot context · Grok coding · reduce tokens · session continuity · SQLite memory · durable context · VS Code AI extension · Cursor AI extension

---

## License

Apache License 2.0 — free and open source.

---

**Stop re-prompting the whole repo.**  
Install Orchestrator Memory, run `/session-start` once, and give every AI the same high-signal project brief.
