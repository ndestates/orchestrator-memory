# Workflow Review from workflows.old

[UPDATED 2026-07-07]

Date: 2026-06-03 — refreshed for full docs alignment. See operations/testing.md and reference/chains.md.
Scope: Evaluate workflows in .github/workflows.old and copy only workflows that fit the current repository.

## Repository constraints observed

- Repository currently contains template/docs assets only.
- No `composer.json`, `package.json`, `VERSION`, or `scripts/` directory are present.
- Manifest runtime is `local` and stack is `generic`.

## Decision summary

Copied to .github/workflows:

See operations/testing.md and reference/chains.md for current state. Vault integration uses same CI gates.

- `release.yml`
  - Reason: generic and useful for tagged releases in any repository.
  - Trigger: tag push (`v*`) and manual dispatch.

- `repository-sync.yml` (adapted)
  - Reason: branch divergence/staleness reporting is useful for repository hygiene.
  - Trigger: daily schedule and manual dispatch.
  - Adaptation: removed dependency/version checks that required project-specific files and scripts.

Not copied:

- `ci.yml`
  - Laravel/PHP/Node/security scripts are project-specific and would fail in this template state.
- `auth-stability-guards.yml`
  - Depends on `scripts/guard-auth-stability.sh` and frontend build artifacts not present here.
- `branch-promotion-prs.yml`
  - Assumes a branch flow (`master -> develop -> staging -> production`) not defined for this project.
- `codeql.yml`
  - Useful later, but currently configured as GHAS-dependent/manual and not essential for this template baseline.

## Follow-up suggestion

When the target stack is chosen (PHP, Node, etc.), add a stack-specific `ci.yml` and optionally enable CodeQL with the proper language matrix and repository security settings.
