---
description: Git and githooks workflow for safe delivery.
argument-hint: Scope of change, branch name, and desired tag (if any)
allowed-tools: Read, Grep, Glob, Bash
---

# Git Workflow Guardrails

Follow the full workflow in [`.github/skills/git-workflow-guardrails/SKILL.md`](../../../.github/skills/git-workflow-guardrails/SKILL.md).

## Grok execution notes
- Always load `/load-cache` or relevant TODO/CONCERNS before starting delivery flow.
- **Before commit/push:** `bash scripts/setup-git-hooks.sh` then ensure `scripts/git-push-secrets-guard.py` passes (hooks enforce on staged files and outgoing commits).
- If workflows touched: run workflow-validate + consider `/github-ci-readiness-expert` or `github-workflow-expert` validate.
- After push, if a run fails: immediately invoke `/github-workflow-expert "diagnose latest failure for <workflow>"` (uses new diagnose-failure.sh for root cause + exact fixes).
- Run `ddev exec bash scripts/ci_security_checklist.sh` when the target app provides it.
- Confirm branch aligns with TODO (branch-context if needed).
- Update TODO via specialist after delivery steps.

All steps produce user progress updates. No shortcuts on gates — especially secrets/env guard (GitGuardian).

User focus (optional): $ARGUMENTS
