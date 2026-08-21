# Project Structure

> Map top-level directories and entry points from scan output + targeted reads. For orchestrator-template repos, include `.grok/`, `chains/`, `LOOP.md`, and `docs/codebase/`.

## Core Sections (Required)

### 1) Top-Level Layout

| Path | Purpose | Key files / notes | Evidence |
|------|---------|-------------------|----------|
| [dir] | [purpose] | [notable files] | [path] |

### 2) Entry Points

| Type | Location | How to run | Evidence |
|------|----------|------------|----------|
| [web/cli/worker/script] | [path] | [command] | [file] |

### 3) Application vs Tooling Paths

- Application source: [paths or N/A for template-only repos]
- Orchestrator / agent tooling: [.grok/, chains/, scripts/, .claude/]
- Documentation cache: [docs/codebase/]
- Work tracking: [TODO/]

### 4) Hidden / Config Directories

| Path | Role | Evidence |
|------|------|----------|
| [.github/, .ddev/, etc.] | [role] | [path] |

## Evidence

- [list concrete paths used to populate this doc]