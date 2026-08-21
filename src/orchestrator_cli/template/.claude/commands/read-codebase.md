---
description: Backward-compatible alias for acquire-codebase-knowledge: map the codebase, detect stack, and populate docs/codebase/ cache. Use for onboarding, cache refresh, or architecture discovery.
argument-hint: Optional focus area, e.g. 'architecture', 'services layer', 'docker', 'full'
allowed-tools: Read, Grep, Glob, Bash
---

# Read Codebase (alias)

Delegates to **acquire-codebase-knowledge** (`.claude/commands/acquire-codebase-knowledge/SKILL.md`).

## Execution

1. Load manifest (`.claude/project-manifest.yaml` or `.claude/project-manifest.yaml`).
2. Follow acquire-codebase-knowledge workflow: run `scripts/scan.py`, populate seven `docs/codebase/` files, validate with inquiry checkpoints.
3. Pass optional user focus from arguments as scope hint.

Output contract, stack detection, and cache locations are defined in the canonical skill — not duplicated here.

Follow project security and runtime rules from `copilot-instructions.md` throughout.

User focus (optional): $ARGUMENTS
