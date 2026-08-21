---
description: "Backward-compatible alias for acquire-codebase-knowledge: map the codebase, detect stack, and populate docs/codebase/ cache. Use for onboarding, cache refresh, or architecture discovery."
name: "Read Codebase"
argument-hint: "Optional focus area, e.g. 'architecture', 'services layer', 'docker', 'full'"
agent: "agent"
tools: ["list_dir", "read_file", "semantic_search", "grep_search", "file_search", "agent", "vscode/memory"]
---

# Read Codebase (alias)

Delegates to **acquire-codebase-knowledge** (`.grok/skills/acquire-codebase-knowledge/SKILL.md`).

## Execution

1. Load manifest (`.claude/project-manifest.yaml` or `.github/project-manifest.yaml`).
2. Follow acquire-codebase-knowledge workflow: run `scripts/scan.py`, populate seven `docs/codebase/` files, validate with inquiry checkpoints.
3. Pass optional user focus from arguments as scope hint.

Output contract, stack detection, and cache locations are defined in the canonical skill — not duplicated here.

Follow project security and runtime rules from `copilot-instructions.md` throughout.