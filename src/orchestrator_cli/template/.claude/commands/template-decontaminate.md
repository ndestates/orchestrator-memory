---
description: Post-deploy, pre-commit gate for forked app repos.
argument-hint: Target path (default cwd) — optional --dry-run
allowed-tools: Read, Grep, Glob, Bash
---

# Template Decontaminate

**Goal:** a deployed fork must carry the **project's** identity, not the template's,
before anything is committed to git. This skill is the gate that guarantees it.

## When to run

- Immediately after `/orchestrator-deploy` or `orchestrator upgrade` on an app.
- As the final step of the `template-deploy` chain (auto-wired).
- Before any commit on a freshly deployed/updated fork.

## Sequence (cache-first)

1. **Resolve project** — slug = basename of target root (e.g. `orchestrator`).
   Stack profile from manifest `stack.profile` or `stack-profiles/manifest-map.yaml`.
2. **Rename to project** (write):
   ```bash
   python3 scripts/customize-skills-for-project.py \
     --project-root <TARGET> --auto-profile --sync
   ```
   Applies `name_replacements` + `stack_replacements` + `{placeholder}` substitution,
   then re-syncs `.github/`, `.claude/`, `.copilot/`.
3. **Hard-gate scan** (read-only):
   ```bash
   bash scripts/scan-template-contamination.sh <TARGET>
   ```
   Greps `.grok/.github/.claude/.copilot` for template residue:
   `ndestates/orchestrator`, `Project Template`, `orchestrator template`, and
   unresolved `{project_name|project_slug|project_title|slug|title}` tokens.
   Writes `reports/security/contamination-*.txt`.
4. **Gate decision:**
   - **Exit 0** → clean → safe to `git add`/commit.
   - **Exit 1** → residue found → **do not commit**. Notify with hit count + report
     path; re-run step 2 (or fix the stack profile) until clean.

The template source repo itself (slug `orchestrator` with `scripts/deploy_grok_to_project.py`)
is skipped — its template identifiers are legitimate.

## Hard gate (non-negotiable)

- Commit only on a **clean** scan (exit 0). Never `--force` past a dirty gate.
- Dry-run first when unsure: `--dry-run` on the customize step shows would-change counts.
- Aligns with CONCERNS §9 (wave blast-radius): decontaminate per app **before** the
  separate `commit-*-wave.sh` step runs.

## Outputs

- `reports/security/contamination-<UTC>.txt` — scan report (clean note or hit lines).
- Updated, project-named `.grok/`, `.github/`, `.claude/`, `.copilot/` surfaces.

## Related

- `customize-skills-for-project.py` — the rename engine.
- `orchestrator-deploy` / `template-deploy` chain — what runs before this gate.
- `scan-template-contamination.sh` — the gate script (also CI-suitable).

User focus (optional): $ARGUMENTS
