# Quickstart

[UPDATED 2026-07-21] — ensure MCP + host tools before first session

## Overview

Get from clone to a working AI session in under 15 minutes. This template has no application runtime — you work with skills, cache, and git.

Full platform install (Windows PowerShell, pip package, per-app CLI): [Installation](installation.md).  
MCP + every host: [Multi-platform MCP and host tools](../guides/multi-platform-mcp-and-host-tools.md).  
Licensing: [Licensing](../reference/licensing.md).

## Before you begin

- Git installed
- Python 3 available on the host (**uv** recommended if `ensurepip` is missing)
- An AI client (Grok, Claude, Copilot, Gemini, Cursor, or ChatGPT/Codex)
- You are on a feature branch (not `master`) for day-to-day work

## Steps

1. Clone the repository and open it in your editor.

2. Run the bootstrap installer (recommended):

   ```bash
   # Linux / macOS / WSL — CLI + host tools (rg) + MCP venv
   bash scripts/install.sh --cli --host-tools --mcp
   ```

   ```powershell
   # Windows PowerShell
   .\scripts\install.ps1 -Cli -HostTools
   # MCP venv is easier inside WSL: wsl -e bash -lc 'cd /path/to/repo && bash scripts/ensure-mcp-host.sh'
   ```

3. Confirm tools:

   ```bash
   rg --version
   bash scripts/ensure-mcp-host.sh --check
   ```

4. **One-time:** set up your operator profile ("who I am"):

   ```bash
   bash scripts/setup-who-i-am.sh
   ```

   Edit `.grok/memories/who-i-am.md`, then run `/multi-ai-best-practices-setup` once.  
   See [Who I am setup](who-i-am-setup.md).

5. Start a session with the default chain:

   ```text
   /chain session-start
   ```

   This loads cache, runs standup, and sets lean response mode. Expect `mcp=yes@dev_only` when MCP is ready.

6. Check today's work file:

   ```text
   TODO/YYYY-MM-DD_TODO.md
   ```

   Use the latest date file in `TODO/`.

7. After editing `.grok/skills/`, sync to other models:

   ```bash
   python3 scripts/sync_grok_to_github_claude.py
   python3 scripts/check_name_alignment.py
   ```

## Verify

- `git branch --show-current` shows your feature branch
- Latest `TODO/*.md` is readable and matches your scope
- `bash scripts/chain-audit.sh` reports score 100/100

## Next steps

- [Installation](installation.md) — full install and per-app CLI
- [Multi-platform MCP and host tools](../guides/multi-platform-mcp-and-host-tools.md) — production MCP + `rg` + every AI host
- [Cache and token savings](../guides/cache-and-token-savings.md) — why lean cache-first sessions stay cheap
- [Daily workflow](../guides/daily-workflow.md) — ongoing session habits
- [Chains and skills](../guides/chains-and-skills.md) — when to use `/chain`
- [Project overview](project-overview.md) — how the pieces fit together

## Related

- [Getting started index](index.md)
- [Licensing](../reference/licensing.md)