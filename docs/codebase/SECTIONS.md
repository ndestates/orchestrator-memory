# Cache section index

[GENERATED 2026-07-02] — run `python3 scripts/generate-cache-sections.py` to refresh.

Grep a heading here, then `Read` that section only. Never load `.codebase-scan.txt` in lean mode.

## `ARCHITECTURE.md`
- Summary: Manifest-first, cache-first **orchestration template** — coordinates AI agents via prompts and skills, not application r
- Sections:
  - Architecture
    - System Purpose
    - Core Model
    - Composition Layers
    - Loop Architecture
      - Half-loop pattern (host + agent)
      - Trusted scheduled chains
    - Sync Architecture
    - Deploy Architecture (template → app repos)
    - MCP Architecture
    - Branch Promotion
    - Key Files
    - Evidence

## `CONCERNS.md`
- Summary: Lens: Security, Operator, Developer
- Sections:
  - Concerns
    - Open Concerns
    - Mitigations
    - Evidence

## `CONVENTIONS.md`
- Summary: - **Manifest first:** read `.github/project-manifest.yaml` (or `.claude/` copy) before deep work.
- Sections:
  - Conventions
    - Session Conventions
    - Branch Conventions
    - Chain Conventions
    - Loop Conventions
    - TODO Conventions
    - Sync & Deploy Conventions
    - CI / Commit Conventions
    - Evidence

## `INTEGRATIONS.md`
- Summary: Lens: Operator, Security
- Sections:
  - Integrations
    - GitHub
      - Workflow Summary
      - Required Repo Settings
    - MCP Server
    - Sync Targets (from `.grok/`)
    - Template Deploy (to app repos)
    - Downstream Template Skills (active only when forked to app repos)
      - App vendor map (`ndestates-io` / `e-ndsign`)
    - Evidence

## `README.md`
- Summary: **Human documentation:** [docs/index.md](../index.md) — navigable guides, reference, and operations.
- Sections:
  - Orchestrator Template Cache Index
    - Project Snapshot
    - What This Repository Contains
    - Cache Files
    - Session Entry Points
    - How To Use This Cache

## `STACK.md`
- Summary: **Orchestrator template** — documentation, prompts, agents, and automation config. No application runtime (no Laravel/No
- Sections:
  - Stack
    - Repository Type
    - Manifest Defaults
    - Tooling
    - MCP Server (`mcp-server/`)
    - AI Surfaces
    - Inventory (counts)
    - Token Policy (lean)
    - Evidence

## `STRUCTURE.md`
- Summary: ```
- Sections:
  - Structure
    - Top-Level Layout
    - `.grok/` (primary — source of truth)
    - `.github/`
    - `.claude/`
    - `mcp-server/`
    - `scripts/` (34 files)
    - `patterns/`
    - Evidence

## `TESTING.md`
- Summary: This template has no application test suite. Validation is **registry/policy audit** driven, plus a small unit test for 
- Sections:
  - Testing
    - Audit Scripts
    - MCP Server Tests
    - CI Checks (GitHub)
    - Manual Verification Gates
    - L1 Loop Rubric (verifier)
    - Evidence

## `.codebase-freshness.txt`
- Lean spine file (read whole file, ≤35 lines)
