# Read Codebase (alias)

Delegates to **acquire-codebase-knowledge** (`.github/skills.github/skills/acquire-codebase-knowledge/SKILL.md/SKILL.md`).

## Execution

1. Load manifest (`.claude/project-manifest.yaml` or `.github/project-manifest.yaml`).
2. Follow acquire-codebase-knowledge workflow: run `scripts/scan.py`, populate seven `docs/codebase/` files, validate with inquiry checkpoints.
3. Pass optional user focus from arguments as scope hint.

Output contract, stack detection, and cache locations are defined in the canonical skill — not duplicated here.

Follow project security and runtime rules from `copilot-instructions.md` throughout.
