# Getting started

[UPDATED 2026-07-21] — host tools + MCP + multi-host (incl. ChatGPT)

New contributors and operators start here.

## Overview

This section helps you get up and running with the orchestrator template quickly. Compatible AI clients: **Grok, Claude Code, GitHub Copilot, Gemini, Cursor, ChatGPT/Codex**.

**Install first:** use the per-app CLI (`orchestrator init` / `upgrade`). Multi-app fleet wave deploy is **not** the default path.

## Before you begin
- Git and Python 3 on your system (uv recommended for MCP venv on hosts without `python3-venv`).
- An AI client configured with the project skills / MCP example for that host.
- **ripgrep** recommended: `bash scripts/install-host-tools.sh --yes`.

## In this section

| Page | Description |
|------|-------------|
| [Installation](installation.md) | Linux/macOS, Windows, host tools (`rg`), MCP ensure, per-app CLI |
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