# Guides

[UPDATED 2026-09-17] — product **3.0.0**; npm-only user install; dead wave-deploy-log link removed

Task-oriented instructions for daily work and maintenance.

## Overview

Guides provide step-by-step instructions for common tasks when using the template.

## Before you begin
- Complete [Installation](../getting-started/installation.md) and the quickstart.
- Load cache with `/chain session-start`.

## In this section

| Page | Description |
|------|-------------|
| [**Multi-platform MCP and host tools**](multi-platform-mcp-and-host-tools.md) | **Production:** ripgrep, ensure-mcp, Grok/Claude/Copilot/Gemini/Cursor/**ChatGPT** |
| [**When to use loops**](when-to-use-loops.md) | Loop vs chain vs session; L1 rules; vault/version-drift scaffolds |
| [**Context-window literacy**](context-window-literacy.md) | **How context works** — lost-in-the-middle, lean rules, anti-patterns, what we will not build |
| [**WebMCP (beta)**](webmcp-beta.md) | **Experimental:** browser page tools for agents (`navigator.modelContext`) — not host MCP |
| [**Multi-workstream**](multi-workstream.md) | Day-scale tracks + diamond recommend — all LLMs |
| [**Multi-workstream setup**](multi-workstream/setup.md) | Register, activate/unhold, focus, diamond multi-lane |
| [**Web cache architecture**](web-cache-architecture.md) | HTTP/CDN/image/document caching — `/web-cache-expert` · `/chain web-cache-review` |
| [**Multi-workstream pre-release**](multi-workstream-prerelease.md) | Historical 1.9.x notes (current product is **3.0.0**) |
| [**Cache and token savings**](cache-and-token-savings.md) | **Why cache-first pays** — lean vs deep, MCP vs full files, measure with meter |
| [**Per-app upgrade**](per-app-upgrade.md) | **After each release:** upgrade your apps one-by-one (no wave) |
| [**Local Ollama (optional BYOM)**](local-ollama.md) | Optional local LLM — host / DDEV / docker-compose install + detect |
| [**Model route — free / open-source**](model-route-free-oss.md) | Suggest Ollama OSS (first) or cloud free when task is low-tier; easy switch |
| [Daily workflow](daily-workflow.md) | Session start, **session-end** (mid-day), **eod-shutdown**, TODO, standup |
| [Chains and skills](chains-and-skills.md) | `/chain`, catalogs, opt-out, new safe chains |
| [Documentation](documentation.md) | Producing and refreshing this doc site (outline-first, vault integration) |
| [Template deploy](template-deploy.md) | Policy detail for `init`/`upgrade` |
| [**Production ship**](production-ship.md) | Tag **3.x** → matching GitHub wheel + npm |
| [**Security flywheel**](security-flywheel.md) | Chrome lifecycle; optional peer apps |
| [**Host-first memory**](host-first-memory.md) | Host CLI + VS Code; any project |
| [**Vault learning expansion**](vault-learning-expansion.md) | **v1.5.0** A/B/C pipes (EOD, TODO query, CI emit) |
| [Knowledge vault](knowledge-vault.md) | Secure self-building graph ledger (`reports/vault/events.jsonl`) for persistent context and compound learning |
| [**LLM Wiki**](llm-wiki.md) | Karpathy-style compounding wiki — session brief, ingest/query/lint, MCP, deploy selection |
| [LLM Wiki plan](../../reports/research/llm-wiki-karpathy-plan.md) | Phased product plan (0–4) |

## Verify
- All links resolve.
- You can follow a workflow end-to-end.

## Next steps

- [When to use loops](when-to-use-loops.md)
- [Context-window literacy](context-window-literacy.md)
- [Cache and token savings](cache-and-token-savings.md)
- [Daily workflow](daily-workflow.md)
- [Multi-workstream](multi-workstream.md)
- [Chains and skills](chains-and-skills.md)
- [Knowledge vault](knowledge-vault.md)

## Related

- [Documentation hub](../index.md)
- [Operations index](../operations/index.md)