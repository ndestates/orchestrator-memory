---
tools: ['search/codebase', 'edit/editFiles']
description: "Bootstrap a generic CI/CD baseline for beta readiness using manifest-driven assumptions."
name: "Setup CI/CD Beta"
argument-hint: "Optional target, e.g. 'github actions only', 'ci baseline', 'release flow'"
agent: agent

---

# Setup CI/CD Beta

Use this prompt to define or implement a minimum CI/CD baseline for beta, without hardcoding a stack.

## Step 1: Read Constraints
Read in order:
1. `.github/project-manifest.yaml`
2. `docs/codebase/README.md`
3. `docs/codebase/CONCERNS.md`
4. Existing workflow files in `.github/workflows/` (if present)
5. Latest TODO file

## Step 2: Propose Baseline
Produce a short plan with these sections:
1. CI Validation: lint/build/test baseline tied to manifest stack.
2. Security Checks: dependency/input-risk checks appropriate to stack.
3. Release Flow: tag/release strategy and branch discipline.
4. Beta Gate: explicit pass/fail checks required before beta.

## Step 3: Implement Minimal Safe Set
If user asks to proceed, implement only the smallest useful workflow set.

Rules:
- Prefer one workflow per purpose.
- Avoid project-specific scripts unless they exist.
- **Node 24 mandatory:** set workflow-level `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`; use Node 24-native actions (`actions/checkout@v6`, `actions/upload-artifact@v7`, `actions/setup-python@v6`). Never use Node 20-era `checkout@v4`, `upload-artifact@v4`, or `setup-python@v5`.
- Ship `scripts/verify_github_actions_node24.py` and run it in CI (chain-audit or deploy gate).
- Pin action versions by major tag (`@v6`, `@v7`); avoid legacy commit SHAs for Node 20 actions.

## Output Format
- `Current State`
- `Proposed CI/CD Baseline`
- `Implementation Delta`
- `Beta Gate`
- `Files Referenced`

Keep output concise and actionable.