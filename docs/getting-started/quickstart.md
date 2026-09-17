# Quickstart

[UPDATED 2026-09-17] — npm install · product **3.0.0**

## Overview

Get a working AI session in under 15 minutes. Install the host CLI with npm, optionally write template files into one app, then run `/chain session-start`.

Full install (BYOK, DDEV, troubleshooting): [Installation](installation.md).  
Licensing: [Licensing](../reference/licensing.md).

## Before you begin

- Node.js 18+ and Python 3.10+
- An AI client (Grok, Claude, Copilot, Gemini, Cursor, or ChatGPT/Codex)
- **Your own** provider accounts / API keys ([BYOK](../reference/bring-your-own-keys.md))

## Steps

1. Install the host CLI (only user method):

   ```bash
   npm install -g @ndestates/orchestrator
   orchestrator version
   orchestrator memory brief --seed
   ```

2. Optional — write template files in one app:

   ```bash
   cd /path/to/app
   npx orchestrator init . --no-pr
   ```

3. **One-time** in that app (if `who-i-am` is present):

   ```bash
   bash scripts/setup-who-i-am.sh
   ```

   Edit `.grok/memories/who-i-am.md`, then run `/multi-ai-best-practices-setup` once.  
   See [Who I am setup](who-i-am-setup.md).

4. Start a session with the default chain:

   ```text
   /chain session-start
   ```

5. Check today's work file:

   ```text
   TODO/YYYY-MM-DD_TODO.md
   ```

   Use the latest date file in `TODO/`.

## Verify

- `orchestrator version` prints **3.0.0** (or the installed 3.x)
- Latest `TODO/*.md` is readable and matches your scope
- `/chain session-start` produces a brief you can paste into any assistant

## Next steps

- [Installation](installation.md)
- [Project overview](project-overview.md)
- [Daily workflow](../guides/daily-workflow.md)

## Related

- [Getting started index](index.md)
- [Documentation hub](../index.md)
