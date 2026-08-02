---
name: read-codebase
description: "Backward-compatible alias for acquire-codebase-knowledge."
argument-hint: "Optional focus, e.g. architecture, services, docker, full"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
  - write_file
---
# Read Codebase (alias)

**Delegates to** `.grok/skills/acquire-codebase-knowledge/SKILL.md` — the canonical skill for codebase mapping, stack detection, and cache population.

## Execution

1. Load and follow **acquire-codebase-knowledge** in full (manifest-first, scan.py, seven templates, validation loop).
2. Pass through any user focus from `$ARGUMENTS` as the optional scope hint.
3. `/read-codebase` and `/acquire-codebase-knowledge` produce the same output contract.

Chains `cache-rebuild` and `documentation-full` invoke `acquire-codebase-knowledge` directly; this alias exists for prompts and habits that still use `/read-codebase`.