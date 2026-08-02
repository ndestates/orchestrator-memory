# Project overview

[UPDATED 2026-07-07] — refreshed (secure vault graph for self-building knowledge, multi-AI best practices, manifest vault paths, compound graph ledger, jersey experts, wave, MCP)

## Overview

The orchestrator template coordinates AI agents through **manifests**, **cache**, **chains**, and **loops** — not through application code. It is designed to be forked into product repositories while keeping the same operational patterns.

## Before you begin

Read [Quickstart](quickstart.md) if you have not run a session yet.

## Architecture

```
project-manifest.yaml  →  paths, token/loop/chain policy
        ↓
docs/codebase/ + TODO/ + STATE.md
        ↓
/chain | /orchestrator | specialist skills
        ↓
Synced targets: .github/, .copilot/skills/, .claude/
```

| Layer | Registry | Purpose |
|-------|----------|---------|
| Manifest | `.github/project-manifest.yaml` | Single source of truth for paths and policy (incl. vault_events_dir) |
| Cache | `docs/codebase/` | Lean context for every session |
| Secure Vault Graph | `reports/vault/events.jsonl` (hash-chained, scrubbed) | Self-building durable knowledge ledger with provenance (via loop-compound) |
| Chains | `CHAIN.md`, `chains/registry.yaml` | On-demand multi-skill workflows |
| Loops | `LOOP.md`, `STATE.md` | Scheduled L1 triage + weekly watches (report-only) |
| Skills | `.grok/skills/` | Grok source; synced to Copilot and Claude |

## Source of truth

| Content | Authoritative path |
|---------|-------------------|
| Skills | `.grok/skills/*/SKILL.md` |
| Prompts | `.grok/prompts/*.md` |
| Agents | `.grok/agents/*.md` |
| Human docs | `docs/` (this site) |
| Agent cache | `docs/codebase/` |

## Branch promotion

`feature/*` → `develop` → `master` via draft PRs (`branch-promotion-prs.yml`).

## Verify

Open [docs/codebase/ARCHITECTURE.md](../codebase/ARCHITECTURE.md) for the detailed cache architecture diagram.

## Next steps

- [Chains and skills](../guides/chains-and-skills.md) — composition patterns
- [Manifest reference](../reference/manifest.md) — manifest field guide
- [Documentation hub](../index.md)

## Related

- [Getting started index](index.md)