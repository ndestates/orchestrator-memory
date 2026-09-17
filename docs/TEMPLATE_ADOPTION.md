# Template Adoption and Update Guide

[UPDATED 2026-09-17] — public product **3.0.0**. Users install with npm; this page is **maintainer / fork** adoption. See [Installation](getting-started/installation.md).

This document explains how to use this orchestrator as a template for your project and how to track and integrate template updates over time.

## Preferred: install into an existing app repo

Preferred for apps (no clone):

```bash
npm install -g @ndestates/orchestrator
npx orchestrator init /path/to/your-app --no-pr --dry-run
npx orchestrator init /path/to/your-app --no-pr
```

From a checkout of the **public** product (maintainer):

```bash
git clone https://github.com/ndestates/orchestrator-memory.git
cd orchestrator-memory
bash scripts/install.sh --cli   # maintainer only
# Windows: .\scripts\install.ps1 -Cli

orchestrator init /path/to/your-app --no-pr --dry-run
orchestrator init /path/to/your-app --no-pr
orchestrator status /path/to/your-app --json
```

Later updates:

```bash
orchestrator upgrade /path/to/your-app --no-pr
# or: bash scripts/orchestrator-app-update.sh /path/to/your-app --no-pr
```

Do **not** use multi-app wave scripts for adoption. See [Installation](getting-started/installation.md).

## Initial Adoption (greenfield fork)

### 1. Fork or Copy This Repository

Option A: Use GitHub's template feature (recommended):

```bash
# On GitHub: click "Use this template" button
# Then clone your new repository
git clone https://github.com/your-org/your-project.git
cd your-project
```

Option B: Manual copy and rebase:

```bash
git clone https://github.com/ndestates/orchestrator-memory.git your-project
cd your-project
git remote rename origin upstream
git remote add origin https://github.com/your-org/your-project.git
git push -u origin master
```

### 2. Customize The Manifest

**Install policy:** `orchestrator init` / `upgrade` never overwrite a customized
`project-manifest.yaml`. On a **new** project (no manifest yet), install seeds one
from the template skeleton and amends it for this app’s stack (`stack.profile`,
framework/language/database, runtime). If a stock “Project Template” residue is
found, only identity/stack fields are amended — local `token_policy` / loop policy
stay. See `scripts/_engine/manifest_bootstrap.py`.

Edit `.github/project-manifest.yaml` for your project (canonical; then
`python3 scripts/sync_manifests.py`):

```yaml
project:
  name: "Your Project Name"
  description: "Your project description"
  default_branch: "master"  # or main

stack:
  framework: "laravel"      # Update to your stack
  language: "php"           # Update to your language
  uses_database: true       # true if you use a database
  database_engine: "mysql"  # mysql | postgres | sqlite | none

runtime:
  environment_manager: "ddev"  # ddev | docker-compose | local
  start_command: "ddev start"
  test_command: "ddev exec php artisan test"
```

### 3. Initialize Your Project Cache

Run the bootstrap installer in the new repo:

```bash
bash scripts/install.sh
# Windows: .\scripts\install.ps1
```

Update cache docs in `docs/codebase/` to match your project structure.

### 4. Customize Agents and Prompts

Adjust agent descriptions in `.github/AGENTS.md` to match your domain.

Keep generic prompts (orchestrator, cache loader, daily standup) but adapt stack-specific ones.

## Tracking Upstream Updates

### Strategy A: Git Remote Tracking (Recommended)

If you used Option B above, you already have `upstream` configured.

Otherwise, add the template as a remote:

```bash
git remote add upstream https://github.com/ndestates/orchestrator-memory.git
git fetch upstream
```

### Strategy B: Manual Comparison

Periodically review:

- <https://github.com/ndestates/orchestrator-memory/commits/master>
- <https://github.com/ndestates/orchestrator-memory/releases>

## Integrating Template Updates

### Selective Integration (Recommended)

Review upstream changes and cherry-pick only relevant commits:

```bash
git fetch upstream
git log --oneline upstream/master ^master | head -20
```

Identify useful commits and cherry-pick:

```bash
git cherry-pick <commit-hash>
```

If conflicts arise, resolve them and preserve your project-specific customizations.

### Full Merge Integration (Use With Caution)

Only for early-stage projects with minimal divergence:

```bash
git fetch upstream
git merge upstream/master --no-commit
# Review changes carefully
git diff --cached
# Revert unwanted changes before committing
git reset HEAD path/to/unwanted/file
git commit -m "chore(template): merge upstream orchestrator updates"
```

Recent additions like the knowledge vault (see guides/knowledge-vault.md) should be adopted via the non-destructive deploy path when forking.

## What To Preserve vs What To Sync

### Always Preserve (Project-Specific)

- `.github/project-manifest.yaml` (your project values)
- `docs/codebase/` content (your architecture notes)
- `TODO/` files (your work tracking)
- Stack-specific agents and prompts
- Your custom workflows in `.github/workflows/`

### Safe To Sync From Upstream

- Generic prompts (orchestrator, cache loader, standup)
- Core agent coordination logic
- `scripts/install.sh` improvements
- Generic workflow templates (release, repository-sync)
- Documentation structure improvements

### Review Before Syncing

- `.github/copilot-instructions.md` (may have project rules)
- `.github/AGENTS.md` (agent list may differ)
- Prompt library index files

## Version Tagging Strategy

Tag your project independently from the template:

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

Optionally reference the upstream template version in your tag notes:

```bash
git tag -a v1.1.0 -m "Release 1.1.0 (based on orchestrator template commit abc123)"
```

## Update Workflow Example

1. Check for upstream updates monthly:

   ```bash
   git fetch upstream
   git log --oneline --graph upstream/master ^master
   ```

2. Review commits and identify useful improvements.

3. Create a feature branch for template sync:

   ```bash
   git checkout -b chore/sync-template-updates
   ```

4. Cherry-pick desired commits:

   ```bash
   git cherry-pick <commit1> <commit2>
   ```

5. Test and validate changes don't break your project.

6. Merge to develop and master per your workflow.

## Common Update Scenarios

### Scenario 1: New Generic Prompt Added

✅ **Safe to adopt**: Cherry-pick the commit adding the new prompt file.

### Scenario 2: Manifest Schema Changes

⚠️ **Review required**: Update your manifest to match new schema but preserve your project values.

### Scenario 3: Agent Coordination Logic Improvements

✅ **Safe to adopt**: Cherry-pick orchestrator prompt improvements.

### Scenario 4: New Stack-Specific Content

❌ **Skip or adapt**: Only adopt if relevant to your stack.

## Rollback Strategy

If an update causes issues:

```bash
git revert <problem-commit>
git push origin <your-branch>
```

Or reset to before the sync:

```bash
git reset --hard <commit-before-sync>
# Force push only if branch is not shared
git push origin <your-branch> --force-with-lease
```

## Questions?

- Review the public product repository: <https://github.com/ndestates/orchestrator-memory>
- Check for issues or discussions in the template repo
- Adapt this guide to your team's workflow

Last updated: 2026-06-03
