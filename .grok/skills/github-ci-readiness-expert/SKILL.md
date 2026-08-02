---
name: github-ci-readiness-expert
description: "GitHub CI/CD branch readiness expert for wave projects."
argument-hint: "Branch/PR target e.g. 'feature/foo → develop' | 'pre-push' | lightstone"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---
# GitHub CI/CD Branch Readiness Expert

**Purpose:** Stop repeat CI failures. Before push or PR, predict which workflows will run on this branch, whether they are structurally valid, and whether project-specific gates will pass.

**Not a replacement for** `/github-workflow-expert` (CRUD) or weekly `/chain github-ci-watch` (L1 report-only). This skill is the **pre-flight gate** tied to the **active branch**.

## Mandatory cross-checks

1. `/load-project-cache-first` — `docs/codebase/INTEGRATIONS.md` workflow table, CONVENTIONS, active TODO **Branch:** line.
2. Run analysis script (always):
   ```bash
   python3 .grok/skills/github-ci-readiness-expert/scripts/ci-branch-readiness.py \
     --write-report --json
   ```
3. Load **project CI specialization** (wave apps):
   - `.grok/skills/github-ci-readiness-expert/references/<slug>-ci.md`
   - Slug = repo directory name (`lightstone`, `google-stats`, …) unless user passes another.
   - Fallback: `references/generic-laravel-ci.md` then `references/ci-readiness-rubric.md`.
4. For policy / branch protection: delegate to `/github-expert` — state "Checked /github-expert".
5. Before any commit/push after fixes: `/git-workflow-guardrails` — **BLOCKED** verdict means do not push.

**Preferred chain:** `/chain ci-branch-readiness` (this skill → github-expert → git-workflow-guardrails).

## Analysis workflow

### Phase 1 — Machine report

`ci-branch-readiness.py` produces:

| Check | Meaning |
|-------|---------|
| `triggers_on_push` | Workflows that run on `git push` to current branch |
| `triggers_on_pr` | Workflows that run on PR **into** `develop` (override with `--pr-target`) |
| `validation_errors` | YAML structure (`workflow-validate.sh` or lite fallback) |
| `node24_errors` | `scripts/verify_github_actions_node24.py` when present |
| `missing_secrets` | `${{ secrets.NAME }}` in workflows but not in `gh secret list` (names only) |
| `local_checks` | `chain-audit.sh`, node24 verify on host |

Report path: `reports/ci/YYYY-MM-DD-<slug>-branch-readiness.md`

### Phase 2 — Project specialization (human/agent)

Read `<slug>-ci.md` and apply **project gates** the script cannot know:

- Stack runtime (DDEV vs container-only CI; Laravel `ci.yml` vs image-build pipelines)
- Jobs that are manual-only (`workflow_dispatch`, `ci-preflight.yml`)
- Path filters — will **this diff** trigger heavy jobs?
- Required local steps before green CI (e.g. `ddev exec php artisan test` on Laravel apps)
- Deploy workflows that must **not** run on feature branches

### Phase 3 — Verdict

| Verdict | Meaning | Push? |
|---------|---------|-------|
| **READY** | Triggers understood; validation green; no blockers | Yes, via guardrails |
| **CONDITIONAL** | Warnings (e.g. gh unavailable, no push triggers but PR OK) | User confirms |
| **BLOCKED** | YAML/node24/secret/local parity failure | Fix first |

### Phase 4 — Fix loop (when BLOCKED)

| Issue | Delegate to |
|-------|-------------|
| Workflow YAML / pins | `/github-workflow-expert` |
| Branch protection / env rules | `/github-expert` |
| Commit/push after fix | `/git-workflow-guardrails` |

Re-run `ci-branch-readiness.py` until READY or accepted CONDITIONAL.

## Wave project index

See `references/wave-projects-ci.md` for slug → specialization file map.

## Output format

```markdown
## CI Branch Readiness — <project> @ <branch>
**Verdict:** READY | CONDITIONAL | BLOCKED

### Will run on push
- ...

### Will run on PR → develop
- ...

### Blockers / warnings
- ...

### Project-specific (from <slug>-ci.md)
- ...

### Next steps
- ...
```

Cite cache files and report path. Never print secret **values**.