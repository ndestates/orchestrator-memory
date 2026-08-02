# Bring your own keys (BYOK) — model providers

**Orchestrator is not a hosted AI model service.** It does **not** supply, rent, or proxy API keys for OpenAI, Anthropic, xAI/Grok, Google Gemini, Azure, or any other model provider.

You must use **your own accounts** and, where an API is required, **your own API keys**.

---

## What this software is

| Layer | What it is | Needs a provider API key? |
|-------|------------|---------------------------|
| **Host CLI** (`orchestrator memory …`) | Local tools: SQLite project memory, vault helpers, init/upgrade | **No** — runs on your machine |
| **VS Code / Cursor extension** | UI that shells out to the host CLI | **No** — same as CLI |
| **Skills / chains / agents** (template) | Instructions your **AI coding host** follows | **Your host’s** subscription or API (see below) |
| **Optional Ollama / local models** | BYOM on your hardware | **No** cloud key (you install models locally) |
| **Optional MCP** | Local or self-hosted tools | Usually **no** vendor LLM key; only if you wire one |

---

## What you must provide

1. **An AI coding environment** you already pay for or control, for example:
   - [Claude Code](https://claude.ai) / Anthropic account  
   - [Grok / xAI](https://x.ai) (Grok Build)  
   - [GitHub Copilot](https://github.com/features/copilot)  
   - [Cursor](https://cursor.com)  
   - Google Gemini / ChatGPT / Codex as you prefer  
2. **API keys only when you choose to call a provider API yourself** (scripts, MCP, custom apps):
   - Create keys in **that provider’s** console under **your** account  
   - Store them in **your** environment or secret manager (never commit them)  
3. **Never put keys into this repository** or open a PR that contains secrets  

Typical env names (examples only — use whatever your provider documents):

```bash
# Examples — create these in YOUR provider accounts; we do not issue them
# export OPENAI_API_KEY=...
# export ANTHROPIC_API_KEY=...
# export XAI_API_KEY=...
# export GOOGLE_API_KEY=...   # or GEMINI_API_KEY
```

---

## What we do **not** do

- We do **not** ship working third-party API keys in releases, wheels, or the VSIX  
- We do **not** require you to send keys to ndestates to use the open-source product  
- Optional **Patreon** support is a donation — **not** a license key and **not** model access  
- Optional **self-hosted license server** (advanced) is separate from model providers  

---

## Privacy

- **Memory** (`reports/memory/`, vault) stays on **your** machine by default  
- Model chats run through **your** chosen host (Claude, Grok, Copilot, Cursor, …) under **their** terms and **your** account  

---

## Related docs

- [Installation](../getting-started/installation.md)  
- [Production ship](../guides/production-ship.md)  
- [Local Ollama (optional BYOM)](../guides/local-ollama.md)  
- [Licensing (Apache-2.0)](licensing.md)  
- [Public product vs private factory](public-private-repos.md)  
