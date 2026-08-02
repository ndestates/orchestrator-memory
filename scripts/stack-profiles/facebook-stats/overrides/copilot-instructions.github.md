# Project AI Agent Instructions

This guide defines practical, security-first operating rules for AI-assisted development in this repository.

# Copilot Instructions — Facebook Stats (facebook-stats)

**Facebook Stats**: Meta Ads analytics and automation platform for real-estate listing campaigns. Python scripts (facebook-business SDK v24) for campaign performance, catalog/product-set sync, audience management, ad rules, rotation/scheduling, custom images, and pixel/CAPI audits. Flask app (`app.py`) + legacy PHP `web/` layer. Stack: Python 3.11 + Flask + MariaDB 10.11 via DDEV + Docker multi-stage images.

These instructions are security-first and practical. Follow them in priority order.

**This file is maintained for GitHub Copilot and GitHub-native tools.**  
The file `.grok/skills/copilot-instructions/SKILL.md` is the Grok-native equivalent. Both are kept in sync. Grok sessions should prefer the `.grok/` version.

## 1) Work Planning and Branch Safety

- At session startup, read the daily TODO before any coding, edits, or runtime commands.
- **Session-start branch rule:** On session-start chains, daily standup prompts, or standup aliases — run `git fetch origin --prune`, then **always** resolve and report the **latest remote branch worked on** (`remote-last`: newest `origin/*` by committer date). Offer a switch when current ≠ `remote-last` (never auto-checkout).
- If a TODO exists for today, follow it.
- If the latest TODO is from an earlier date, carry it forward to today's TODO file and continue from there.
- Work on the current feature branch, not master.
- Before edits or task runs, confirm you are on the latest remote state for the intended branch.

## 2) DDEV Runtime Rules

### 2.0) Hard rule: All local commands run via DDEV (mandatory)

When working locally on this repository, all project commands MUST be executed inside the DDEV runtime.

- Use `ddev exec <command>` for application code, dependencies, database, or runtime tooling.
- Do NOT run `python3`, `pip`, `php`, `composer`, or `mysql` on the host for project work.
- Host-only exceptions: `git`, `gh`, `docker` image builds, `doctl` for prod operations — state why first.
- Tests: `ddev exec python run_tests.py` only.
- DDEV control commands (`ddev start`, `ddev stop`, `ddev status`, etc.) run on the host.

### 2.1) DDEV lifecycle

- Check `ddev status` before project commands.
- If not running: baseline `git status`, `ddev start`, re-check `git status`, report hook side effects.
- Create tomorrow's TODO before `ddev stop` when ending a session.

### Python Environment Rule (Inside DDEV)

- Default: `ddev exec python3 scripts/<script>.py`, `ddev exec python run_tests.py`.
- Do not use host venv unless explicitly requested.

## 3) Mandatory Security Checklist Trigger

Run security checklist when dependencies change or when touching Facebook credentials, `web/` auth, feeds/catalogs, or logging paths.

- Never commit tokens, app secrets, or ad account IDs.
- Follow `.grok/rules/00-security.md` and `02-facebook-marketing.md`.
- For commits: use `git-workflow-guardrails` ordering.

## 4) Shell Artifact Hygiene

After complex shell commands, run `git status --short` and clean accidental files. Prefer script files over inline shell for multi-line logic.

## 5) Data Safety (Critical)

- Never run destructive operations on live production `facebook_stats` data.
- Tests use safe DB configuration via `run_tests.py`.
- Confirm DB target before any import/export or schema work.
- Preserve rotation/catalog/pixel automation invariants.

## 6) Mandatory Pre-Test Checklist

1. Use DDEV + `run_tests.py`.
2. Review `tests/conftest.py` and `pyproject.toml` markers.
3. For DB work, use DDEV copies from `backup/latest-facebook-stats-db.sql.gz` only.
4. State DB target and scripts before API-touching runs.

## 7) Recovery-First Policy

On unexpected data loss: stop, restore to isolated DDEV DB from backup, validate, then promote. Re-run analyzer scripts.

## 8) Auth and Security Regression Guardrails

- Protect `web/` sessions and `src/config.py` credential loading.
- Run targeted checks after dependency or deploy changes.

## 9) Test Scope (pytest)

- `ddev exec python run_tests.py` (optional `--coverage`).
- For Meta/Facebook script changes: run script + analyzer and cite dated report output.

## 10) Communication and Command Examples

```bash
ddev exec python3 scripts/campaign_rotation_manager.py
ddev exec python3 scripts/catalog_updater.py
ddev exec python run_tests.py
```

## 11) AI Engineering Maturity

Maintain shared `.grok/` / `.github/skills/` context, cache-first workflows, and security gates. See `ai-engineering-maturity` skill.

**Primary ops skills:** `facebook-stats-ops`, `facebook-ads-marketing-expert`, `ddev-local-runtime`, `test-safety-agent`.