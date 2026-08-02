# Project AI Agent Instructions

This guide defines practical, security-first operating rules for AI-assisted development in this repository.

# Copilot Instructions — {title} ({slug})

**{title}** (`{slug}`): Laravel 12 + Filament application. Manifest-first, cache-first AI scaffolding via `.grok/` skills, chains, and loops. **Read `.github/project-manifest.yaml` first** for `stack`, `paths`, `runtime`, and `token_policy`.

These instructions are security-first and practical. Follow them in priority order.

**This file is maintained for GitHub Copilot and GitHub-native tools.**  
The file `.grok/skills/copilot-instructions/SKILL.md` is the Grok-native equivalent. Both are kept in sync. Grok sessions should prefer the `.grok/` version.

## 1) Work Planning and Branch Safety

- At session startup, read the daily TODO before any coding, edits, or runtime commands.
- **Session-start branch rule:** On session-start chains, daily standup prompts, or standup aliases — run `git fetch origin --prune`, then **always** resolve and report the **latest remote branch worked on** (`remote-last`: newest `origin/*` by committer date). Offer a switch when current ≠ `remote-last` (never auto-checkout).
- Work on the current feature branch, not master.

## 2) DDEV Runtime Rules (mandatory)

- All application commands run via DDEV: `ddev exec`, `ddev composer`, `ddev artisan`, `ddev mysql`, `ddev npm`, etc.
- Do not run `php`, `composer`, `artisan`, `mysql`, or `npm` on the host for project work.
- If DDEV is not running, `ddev start` before project commands.

## 3) Security Checklist

- Run security checklist when dependencies change or form/auth code changes.
- Follow `git-workflow-guardrails` for commit/push gates.

## 4) Data Safety

- Never run destructive operations on live `db`.
- Tests only against `test` or `:memory:` databases.

## 5) Auth Regression

- Treat login and 2FA flows as critical; do not change without explicit request.
