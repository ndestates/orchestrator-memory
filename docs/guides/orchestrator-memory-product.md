# Orchestrator Memory — product straplines & popularization

[UPDATED 2026-08-01] · Product / extension **2.1.0** (semver MINOR) · Host CLI **2.1.0** · Apache-2.0 freeware

**Marketplace:** https://marketplace.visualstudio.com/items?itemName=ndestates.orchestrator-memory  

**★ Full instructions (SQLite memory + vault) — encourage every user to read:**  
[extensions/vscode-orchestrator/INSTRUCTIONS.md](../../extensions/vscode-orchestrator/INSTRUCTIONS.md)

Marketplace page + install channels:  
[extensions/vscode-orchestrator/README.md](../../extensions/vscode-orchestrator/README.md)

---

## Listing fields (copy-paste)

| Field | Value |
|-------|--------|
| **Name** | Orchestrator Memory — AI token cache |
| **Publisher** | ndestates |
| **Item ID** | `ndestates.orchestrator-memory` |
| **License** | Apache-2.0 |
| **Categories** | AI, Machine Learning, Chat, Other |

### One-liner (own this)

> Local project memory for AI coding — paste a short brief, stop re-prompting the whole repo.

### Alternatives (same idea)

- Session start in 30 seconds, not 10 minutes of context paste.  
- Same project brief in Cursor and Claude.  
- Memory stays on your machine.  
- Portable AI coding memory / token cache for agents.

### Short description (package.json / Marketplace)

> Local project memory for AI coding — paste a short brief, stop re-prompting the whole repo. SQLite + vault; Claude, Grok, ChatGPT, Gemini, Copilot & Cursor. Free Apache-2.0.

### What it does (long)

Local memory + cache layer for AI coding sessions. Durable project context in a small **SQLite** DB (and optional **vault**) so assistants (Claude, Grok, ChatGPT, Gemini, Copilot, Cursor, etc.) start from a short reusable brief instead of re-pasting large context every time — lower token use, faster session start, better continuity.

### Core features (bullet)

- **SQLite store** — `reports/memory/memory.db` (project) or `~/.orchestrator/` (global); gitignored  
- **Optional vault dual-write** — scrubbed events/lessons in `reports/vault/events.jsonl`  
- **Inbox ingest** — `reports/memory/inbox/`  
- **Commands** — Memory Brief, Query, Ingest, Seed, Status, Serve; **Command Hub** for `/chain` + skills  
- **Copy for Claude / Cursor / Copilot** + Export `MEMORY.md`  
- **Privacy** — local only; no cloud upload of memory data  

### Requirements (one line)

Thin wrapper around the Orchestrator **host CLI** (install once via uv, pip, npm, or install script). In-app **Setup / Install CLI** copies the command for you.

---

## In-app: not difficult

| UX | Purpose |
|----|---------|
| Status bar **Memory** | Opens Command Hub |
| `Ctrl/Cmd+Shift+O` | Command Hub (memory · /chain · skills) |
| `Ctrl/Cmd+Shift+M` | Memory Brief |
| After Brief | Copy · Claude · Cursor · Copilot · MEMORY.md · /chain session-start |
| Run /chain … | QuickPick from `chains/registry.yaml` → clipboard |
| Run skill … | QuickPick slash skills → clipboard |
| Setup wizard | Detect CLI; copy uv/pip install |

---

## Audience order

1. Multi-tool users (Cursor + Claude Code + Copilot + ChatGPT in one week)  
2. Token-sensitive freelancers / indie hackers  
3. Teams on Claude/GPT API bills  
4. Later: enterprise local-only / no-upload memory  

**Avoid in first sentence:** “orchestrator infrastructure,” “vault dual-write,” “host CLI.” Lead with outcomes; setup is second.

---

## Popularize (summary)

1. **Story** — token relief + multi-AI continuity, not another chat panel.  
2. **Product** — activation = first Brief in 10 minutes; copy/export; Setup wizard (this release).  
3. **Marketplace SEO** — keywords: project memory, token savings, Claude Code, Cursor memory, SQLite, local AI memory.  
4. **Content** — before/after token counts; “four AIs, one brief”; 60–90s demo.  
5. **Channels** — r/Cursor, r/ClaudeAI, X AI-coding, Show HN when one-click install is tight.  
6. **Virality** — shareable brief footer (opt-out later), MEMORY.md export, PR context action later.  
7. **Lane** — thin local memory layer vs multi-agent dashboards / cloud RAG.  

### Metrics

- Activation: install → first Memory Brief ≤ 10 min  
- Retention: Query/Status in week 2  
- Share: copies / MEMORY.md exports  
- Marketplace: install→uninstall, ratings  

### 30-day sketch

| Week | Focus |
|------|--------|
| 1 | Convert — Setup wizard, Hub, copy brief, Marketplace rewrite + GIF |
| 2 | Proof — dogfood token before/after; community posts |
| 3 | Amplify — short demos; creator outreach |
| 4 | Retain — soft review after 3 briefs; weekly changelog |

Full growth playbook lives with marketing notes; **engineering SSOT** for install remains the extension README.

---

## Related

- [Host-first memory](host-first-memory.md)  
- [Production ship](production-ship.md)  
- [Always-on memory engine](always-on-memory.md)  
