# CI Readiness Rubric (all projects)

## Universal blockers

- Workflow YAML fails `workflow-validate.sh`
- `verify_github_actions_node24.py` fails (legacy action pins, missing `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`)
- `${{ secrets.* }}` referenced but name missing from `gh secret list`
- `chain-audit.sh` fails when chain registry is in scope
- Pushing from `master`/`develop` for feature work (branch policy)

## Universal warnings

- No workflows trigger on push (PR-only CI) — confirm PR target
- `gh` not authenticated — secret gap check skipped
- Path filters on workflows — diff may not trigger jobs
- `workflow_dispatch` only — manual smoke required (`ci-preflight.yml` pattern)

## Pre-push checklist

1. Current branch matches TODO **Branch:** line
2. Run `ci-branch-readiness.py --write-report`
3. Run project-local tests per specialization (DDEV when applicable)
4. `/git-workflow-guardrails` only when verdict READY or accepted CONDITIONAL