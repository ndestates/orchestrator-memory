# Cache section index

[GENERATED 2026-08-16] — run `python3 scripts/generate-cache-sections.py` to refresh.

Grep a heading here, then `Read` that section only. Never load `.codebase-scan.txt` in lean mode.

## `ARCHITECTURE.md`
- Summary: > Lens: Product, Developer, Operator — evidence from README, `src/orchestrator_cli/`, `extensions/`, `mcp-server/`, LOOP
- Sections:
  - Architecture
    - System Purpose
    - Core Model
    - Composition Layers
    - Session architecture
    - Loop architecture
      - Half-loop (host + agent)
    - Sync architecture
    - Deploy architecture (template → one app)
    - Product packaging
    - MCP architecture
    - Branch promotion
    - Key files
    - Evidence

## `CONCERNS.md`
- Summary: Lens: Security, Operator, Developer, Product
- Sections:
  - Concerns
    - Open Concerns
    - Mitigations
    - Evidence

## `CONVENTIONS.md`
- Summary: > Lens: Developer, Operator — evidence from manifest `token_policy` / `chain_policy` / `loop_policy`, CLAUDE.md, session
- Sections:
  - Conventions
    - Session Conventions
      - Session command split
    - Branch Conventions
    - Chain Conventions
    - Loop Conventions
    - TODO Conventions
    - Sync & Deploy Conventions
    - Version lockstep
    - CI / Commit Conventions
    - Provider prompt caching (direct API calls)
    - Evidence

## `INTEGRATIONS.md`
- Summary: > Lens: Operator, Security — evidence from `.github/workflows/`, `mcp-server/`, `package.json`, `services/license-api/RE
- Sections:
  - Integrations
    - GitHub
      - Workflow summary
      - Required repo settings
    - VS Code Marketplace
    - MCP Server
    - Memory and vault
    - Optional license API
    - Sync targets (from `.grok/`)
    - Template deploy (to app repos)
    - Downstream vendor skills (app repos only)
    - Evidence

## `README.md`
- Summary: **Human documentation:** [docs/index.md](../index.md) — guides, reference, operations (knowledge-vault, daily-workflow, 
- Sections:
  - Orchestrator Template Cache Index
    - Project Snapshot
    - What This Repository Contains
    - Cache Files
    - Session Entry Points
    - How To Use This Cache

## `STACK.md`
- Summary: > Lens: Operator, Developer — evidence from manifest, `pyproject.toml`, `package.json`, `extensions/vscode-orchestrator/
- Sections:
  - Stack
    - Repository Type
    - Manifest vs scan
    - Product versions (lockstep)
    - Languages and runtimes
    - Tooling
    - AI surfaces (this install)
    - Token policy (lean)
    - Inventory (2026-08-16)
    - Evidence

## `STRUCTURE.md`
- Summary: > Lens: Developer — evidence from `scan.py` `=== TREE ===` and repo listing 2026-08-16.
- Sections:
  - Structure
    - Top-Level Layout
    - `.grok/` (primary)
    - Other AI surfaces
    - Product code
    - `scripts/`
    - `tests/`
    - Evidence

## `TESTING.md`
- Summary: > Lens: Developer, Security — evidence from `pyproject.toml`, `tests/`, `mcp-server/tests/`, `.github/workflows/tooling-
- Sections:
  - Testing
    - Commands
    - Layout
    - Audit scripts (still required)
    - CI gates
    - Safety rules
    - Manual verification
    - L1 loop rubric (verifier)
    - Evidence

## `.codebase-freshness.txt`
- Lean spine file (read whole file, ≤35 lines)
