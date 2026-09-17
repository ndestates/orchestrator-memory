# Getting started

[UPDATED 2026-09-17] — npm install · product **3.0.0**

New contributors and operators start here.

## Overview

This section helps you get up and running with Orchestrator Memory quickly. Compatible AI clients: **Grok, Claude Code, GitHub Copilot, Gemini, Cursor, ChatGPT/Codex**.

**Install first:** `npm install -g @ndestates/orchestrator`. Then optionally write template files with `npx orchestrator init` / `upgrade`. Multi-app fleet wave deploy is **not** the default path.

## Before you begin
- Node.js 18+ and Python 3.10+
- An AI client configured with **your** accounts / API keys ([BYOK](../reference/bring-your-own-keys.md))
- **ripgrep** recommended after template files exist in an app (`rg` via apt/brew; see [Installation](installation.md))

## In this section

| Page | Description |
|------|-------------|
| [Installation](installation.md) | **npm only** for users; maintainer/private paths quarantined |
| [Quickstart](quickstart.md) | Run your first session with `/chain session-start` |
| [Who I am setup](who-i-am-setup.md) | Persistent operator profile for multi-AI sessions |
| [Project overview](project-overview.md) | Manifest, cache, chains, and loops explained |
| [Multi-platform MCP](../guides/multi-platform-mcp-and-host-tools.md) | Production MCP + host tools for every AI product |
| [Licensing](../reference/licensing.md) | Optional license gate for init/upgrade |

## Verify
- You can open the latest `TODO/*.md`.
- Links in this index resolve.
- `orchestrator version` works after CLI install (or `python -m orchestrator_cli version`).

## Next steps

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [Project overview](project-overview.md)
- [Guides index](../guides/index.md)

## Related

- [Documentation hub](../index.md)
- [Guides index](../guides/index.md)