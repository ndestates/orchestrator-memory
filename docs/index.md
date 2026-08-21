# Orchestrator Template Documentation

[UPDATED 2026-07-21] — **v1.8.8** multi-platform MCP + ChatGPT surface + host tools (ripgrep)

This documentation explains how to use the **orchestrator template** — a manifest-first, cache-first system for AI-assisted delivery. It ships skills, prompts, agents, loops, and chains synced across **Grok, Claude Code, GitHub Copilot, Gemini, Cursor, and ChatGPT/OpenAI**.

**Bring your own keys:** You must have **your own** accounts (and API keys where needed) with those providers. Orchestrator does not supply model API keys. See [Bring your own keys](reference/bring-your-own-keys.md).

**Install path:** [Installation](getting-started/installation.md) · **BYOK:** [Bring your own keys](reference/bring-your-own-keys.md) · **Upgrade your apps:** [Per-app upgrade](guides/per-app-upgrade.md) · **MCP + hosts:** [Multi-platform MCP and host tools](guides/multi-platform-mcp-and-host-tools.md) · **Licensing:** [Licensing](reference/licensing.md).  
Per-app `orchestrator init` / `upgrade` only — multi-app wave is blocked by default (abandoned for routine releases).

For repository overview, see the [root README](../README.md).

## Getting started

- [Overview](getting-started/index.md) — what this project is and who it is for
- [Installation](getting-started/installation.md) — Linux/macOS, Windows PowerShell, package CLI, host tools, MCP ensure, per-app install
- [Bring your own keys](reference/bring-your-own-keys.md) — **required:** your own model-provider accounts and API keys
- [Quickstart](getting-started/quickstart.md) — first successful session in under 15 minutes
- [Project overview](getting-started/project-overview.md) — architecture at a glance

## Verify

- Hub links work (≤2 clicks to any section).
- Installation and licensing pages are linked from Getting started and Reference.

## Guides

- [Guides index](guides/index.md) — task-oriented how-tos
- [**Multi-platform MCP and host tools**](guides/multi-platform-mcp-and-host-tools.md) — **production:** `rg`, ensure-mcp, every AI client (incl. ChatGPT)
- [**WebMCP (beta)**](guides/webmcp-beta.md) — **experimental:** browser page tools for agents (not host MCP)
- [**Multi-workstream**](guides/multi-workstream.md) — day-scale tracks + agent graphs; **per-LLM guides** (Grok/Claude/Copilot/ChatGPT/Gemini/Cursor)
- [**Cache and token savings**](guides/cache-and-token-savings.md) — lean vs deep loads, MCP vs full files, how to measure
- [**When to use loops**](guides/when-to-use-loops.md) — loop vs chain; L1; scaffolded vault/version watches
- [Daily workflow](guides/daily-workflow.md) — sessions, TODO, standup, Monday watches
- [Chains and skills](guides/chains-and-skills.md) — composition, scheduled chains, opt-out
- [Documentation](guides/documentation.md) — how this doc site is maintained (full update process, Phase 2.5 outline-first)
- [**Per-app upgrade**](guides/per-app-upgrade.md) — **after each orchestrator release**, upgrade apps one-by-one
- [**Local Ollama (optional BYOM)**](guides/local-ollama.md) — optional local LLM install (host / DDEV / compose)
- [Template deploy](guides/template-deploy.md) — policy detail for init/upgrade
- [Wave deploy log](guides/wave-deploy-log.md) — historical fleet records only
- [Knowledge vault](guides/knowledge-vault.md) — secure self-building graph ledger (reports/vault, compound integration)
- [Prompt injection (installed apps)](guides/prompt-injection-installed-apps.md) — trust boundary, guardrails check, product AI
- Compliance: Jersey DP/AML experts + safe chains + DPIAs (see guides/ + .grok/skills/jersey-*)

## Reference

- [Reference index](reference/index.md) — manifests, chains, skills, licensing, platform surfaces
- [**Bring your own keys (BYOK)**](reference/bring-your-own-keys.md) — **your** model accounts & API keys required
- [Platform surfaces](reference/platform-surfaces.md) — Grok · Claude · Copilot · Gemini · Cursor · **ChatGPT**
- [Multi-platform tool use](reference/tools/multi-platform-tool-use.md) — MCP client configs per host
- [Manifest](reference/manifest.md) — `project-manifest.yaml` fields (incl. vault_events_dir, vault_ledger)
- [Licensing](reference/licensing.md) — Apache-2.0 freeware; optional Patreon donations
- [Chains](reference/chains.md) — chain catalog and steps
- [Skills](reference/skills.md) — Grok skill catalog (incl. vault synthesis, loop-compound graph)

## Operations

- [Operations index](operations/index.md) — testing and delivery
- [Testing](operations/testing.md) — audit scripts and CI gates
- [Delivery](operations/delivery.md) — branches, PRs, promotion

---

## Next steps

- [Installation](getting-started/installation.md)
- [Quickstart](getting-started/quickstart.md)
- [Licensing](reference/licensing.md)

**Agent cache** (for AI sessions): [docs/codebase/README.md](codebase/README.md)