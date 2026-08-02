---
name: copilot-instructions
description: 'Core operational instructions for facebook-stats (DDEV, security, data safety, TODO lifecycle, branch rules, Facebook/Meta marketing guardrails, etc.). This is the native Grok skill (primary for Grok sessions). The `.github/copilot-instructions.md` version is maintained separately for GitHub Copilot users. Always reference the Grok version in .grok/ contexts.'
user-invocable: true
disable-model-invocation: false
---

# Copilot Instructions — Facebook Stats (facebook-stats) (Grok Native)

**Facebook Stats**: Meta Ads analytics and automation platform for real-estate listing campaigns. Python scripts (facebook-business SDK v24) for campaign performance, catalog/product-set sync, audience management, ad rules, rotation/scheduling, custom images, and pixel/CAPI audits. Flask app (`app.py`) + legacy PHP `web/` layer. Stack: Python 3.11 + Flask + MariaDB 10.11 via DDEV + Docker multi-stage images.

These instructions are security-first and practical. Follow them in priority order.

**This is the primary version for Grok.**  
The file `.github/copilot-instructions.md` is the equivalent maintained for GitHub Copilot (and GitHub-native tools). Both are kept in sync for dual compatibility. Grok sessions should prefer this `.grok/skills/copilot-instructions/SKILL.md`.

## 1) Work Planning and Branch Safety

- At session startup, read the daily TODO before any coding, edits, or runtime commands.
- **Session-start branch rule:** On `/chain session-start`, `/daily-standup-with-cache`, `/daily-standup`, or standup aliases — run `git fetch origin --prune`, then **always** resolve and report the **latest remote branch worked on** (`remote-last`: newest `origin/*` by committer date). Offer a switch when current ≠ `remote-last` (never auto-checkout). See `daily-standup-with-cache` Step 2.
- If a TODO exists for today, follow it.
- If the latest TODO is from an earlier date, carry it forward to today's TODO file and continue from there.
- Work on the current feature branch, not master.
- Before edits or task runs, confirm you are on the latest remote state for the intended branch.

## 2) DDEV Runtime Rules

### 2.0) Hard rule: All local commands run via DDEV (mandatory)

When working locally on this repository, all project commands MUST be executed inside the DDEV runtime. The host shell is not a supported execution environment for project work.

- Use `ddev exec <command>` for any command that touches application code, dependencies, the database, or runtime tooling.
- Use the dedicated DDEV wrappers when available: `ddev php`, `ddev composer`, `ddev mysql`, `ddev exec python3`, `ddev exec pip`.
- Do NOT run `php`, `composer`, `python3`, `pip`, or `mysql` directly on the host. If a host-only invocation is unavoidable (e.g. `git`, `gh`, `docker` for image build/push, `doctl` for prod DB, repo-wide `find`/`grep`), state why before running it.
- If DDEV is not running, follow section 2.1 (start it) before issuing any project command.
- For tests, prefer `ddev exec python run_tests.py` over host invocations. Database tests must target a safe test database per section 6.
- For Python tooling, see "Python Environment Rule (Inside DDEV)" below — `ddev exec python3 ...` is the only supported path.
- The only project command exempt from DDEV is the DDEV control surface itself: `ddev start`, `ddev stop`, `ddev status`, `ddev describe`, `ddev restart`, `ddev import-db`, `ddev export-db`.

Rationale: keeps the local toolchain, PHP/Python versions, extensions, env vars, and DB engine identical to CI and production-adjacent environments. Bypassing DDEV produces drift bugs that don't reproduce on the server.

### 2.1) DDEV lifecycle

- Check DDEV status before running project commands.
- If DDEV is not running:
  1. Run `git status --short` and treat it as a baseline.
  2. Run `ddev start`.
  3. Run `git status --short` again and compare.
  4. If startup created file changes, report them and ask whether to keep or discard before continuing.
- Keep DDEV running for the session unless the user asks to stop it.
- At session end, when stopping DDEV, ensure tomorrow's TODO file exists. If it does not exist, create it before or immediately after `ddev stop`.
- Assume `ddev start` can change tracked files (hooks, pip install, DB import). Do not include those side effects in commits unless explicitly requested.

### Session Lifecycle Checklist

Startup (mandatory):
- Find the latest `TODO/*_TODO.md` file in `TODO/`.
- If today's TODO file is missing, create `TODO/YYYY-MM-DD_TODO.md` by carrying forward open items from the latest TODO.
- Read today's TODO and state the active work items before proceeding.

Shutdown (mandatory when user asks to stop DDEV):
- Compute tomorrow's date and check for tomorrow's TODO file.
- If missing, create it with carried-forward open items and a short "next session" section.
- Run `ddev stop` only after confirming tomorrow's TODO exists.

### Python Environment Rule (Inside DDEV)

- Treat Python tooling as running inside the DDEV runtime for this repo.
- Prefer `ddev exec python3 ...` and `ddev exec pip ...` over host Python/venv commands.
- Do not rely on host venv activation unless the user explicitly asks for host-only execution.
- When running Python scripts in this project, default to:
  - `ddev exec python3 scripts/<script>.py ...`
  - `ddev exec python run_tests.py`
  - `ddev exec pip install -r requirements.txt` (post-start hook usually handles this)

## 3) Mandatory Security Checklist Trigger

Security checklist execution is mandatory whenever either condition is true:

- Dependencies changed (`requirements.txt`, `pyproject.toml`, composer if PHP touched).
- Any change touches Facebook credentials handling, auth in `web/`, feed/catalog output, or script paths that log API responses.

Execution source of truth:
- For commit/push/release flows, follow `.grok/skills/git-workflow-guardrails/SKILL.md` for exact commands and ordering.
- Outside git delivery flows, run `./scripts/ci_security_checklist.sh` when present and review `reports/security/` artifacts.

Checklist expectations:
- Never commit Facebook access tokens, app secrets, or ad account IDs (`act_...`).
- Review requirements/dependency changes for known vulnerabilities.
- Check for risky raw output paths that could leak tokens or PII in reports/logs.
- Review artifact threat scan (`reports/security/artifact-threat-*.txt`) when available.
- Review MCP server threat scan (`reports/security/mcp-threat-*.txt`) for skills/agents/prompts changes.
- Follow `.grok/rules/00-security.md` and `02-facebook-marketing.md` at all times.

## 4) Shell Artifact Hygiene

After shell commands that use patterns or special characters (especially `rg`, `grep`, or commands containing `(`, `)`, `|`, `->`, `{`), immediately run:

- `git status --short`

If accidental files were created by shell parsing, unstage/delete them before continuing. Prefer `/script-not-shell` for multi-line logic.

## 5) Data Safety (Critical)

- Never run destructive operations against live `facebook_stats` production data.
- Use test-only databases for tests (`run_tests.py` targets safe DB configuration).
- Before tests, confirm the database target is not production.
- If DB target is production or ambiguous, stop and report risk.
- Prefer non-destructive checks and validated copies for DB experiments.
- Ask for explicit confirmation before any operation that could alter live campaign tracking, catalog, or auth data.
- Never weaken rotation/catalog/pixel automation invariants without validation scripts.

## 6) Mandatory Pre-Test Checklist

1. Confirm you are using DDEV and `run_tests.py` (not ad-hoc host pytest against prod).
2. Verify test configuration in `pyproject.toml` and `tests/conftest.py`.
3. Before risky DB operations, work from `backup/latest-facebook-stats-db.sql.gz` copies in DDEV only.
4. State which database and scripts will be used before running tests or automation against real APIs.

## 7) Recovery-First Policy

If live counts or campaign/catalog state drop unexpectedly:

1. Stop all test/import/migration actions.
2. Restore into an isolated DDEV database first from `backup/*.sql.gz`.
3. Validate counts and table integrity (campaign tracking, catalog-related tables).
4. Restore validated data into the intended target only after verification.
5. Re-check with relevant analyzer scripts (`analyze_active_rules.py`, `check_catalogs.py`, etc.).

## 8) Auth and Security Regression Guardrails

- Treat `web/` session auth and Facebook credential loading (`src/config.py` + `.env`) as critical.
- Do not change auth or token handling unless explicitly requested.
- After dependency or deploy changes, run targeted checks on web login paths and a safe script dry-run.
- Flag high/critical vulnerability findings immediately.

## 9) Test Scope (pytest)

- Primary test runner: `ddev exec python run_tests.py` (add `--coverage` when relevant).
- Script-focused tests live under `tests/test_*.py` with pytest markers (`unit`, `integration`, `api`, `slow`).
- Keep business logic and automation invariants unchanged unless explicitly requested.
- For Facebook/Meta changes, run the affected script plus its analyzer/validation pair and cite dated report output.

## 10) Communication and Command Examples

- Provide commands in plain copyable form.
- Default validation examples:
  ```bash
  ddev exec python3 scripts/campaign_rotation_manager.py
  ddev exec python3 scripts/catalog_updater.py
  ddev exec python run_tests.py
  ```

## Grok-specific Notes

- This skill is the Grok-native home for these rules (see also the `.github/` version for Copilot users).
- Cross-reference dedicated skills: `facebook-stats-ops`, `facebook-ads-marketing-expert`, `ddev-local-runtime`, `git-workflow-guardrails`, `test-safety-agent`, `security-audit-agent`.
- Always cross-reference `docs/codebase/CONVENTIONS.md`, `TESTING.md`, `STACK.md`, and `load-project-cache-first` for full context.
- Laravel/Filament/PayPal/SES skills in `.grok/skills/` are optional template bundles — not the primary stack for this repo.

## 11) AI Engineering Maturity (8 Stages)

This project adopts the team/organization-centric "8 stages of AI engineering maturity" framework (https://upsun.com/blog/8-stages-ai-engineering-maturity/). AI amplifies existing practices — DDEV, pytest, security, cache discipline, shared `.grok/` context, and Facebook automation guardrails.

**Key principles:**
- Shared context engineering first: maintain `.grok/skills/`, prompts, agents, `docs/codebase/`, TODO carry, and `chains/registry.yaml`.
- Security and governance before scale: new skills/agents/MCP usage triggers checklist + MCP threat scans.
- Spec/context-first + evals as gates: use cache + branch-context + test-safety before risky automation or deploy work.
- When extending `.grok/` or using subagents: invoke `/ai-engineering-maturity` for stage assessment.

Use `/ai-engineering-maturity` for detailed guidance. Cross-reference `daily-standup-with-cache` and `git-workflow-guardrails`.