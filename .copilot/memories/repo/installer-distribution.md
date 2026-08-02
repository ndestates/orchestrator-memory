# Installer distribution (spine memory)

**Updated:** 2026-07-11

## Do not miss

PR **#116** (merged to `develop` 2026-07-09) already delivered:

- Fleet wave **disabled by default** (`auto_deploy: false`, `ORCHESTRATOR_WAVE_DEPLOY_APPROVED=1` override only)
- Per-app path: `orchestrator init` / `upgrade`
- Windows: `scripts/install.ps1` (`-Cli`, later `-Npm`)
- Bash: `scripts/install.sh` (`--cli`, later `--npm`)
- License validate server: `orchestrator license-server`
- Docs: `docs/getting-started/installation.md`, `docs/reference/licensing.md`

## Residual ported 2026-07-11 (from #117 branch, not full merge)

- npm package `@ndestates/orchestrator` (`package.json`, `bin/orchestrator.js`, `scripts/npm/postinstall.js`)
- `licensing_policy` / `first_party` / `defaults` CLI modules
- Kept #116 `license_server` (do **not** take #117 deletion of it)

## Product policy

- **No automated fleet deploy**
- Fleet **deprecated** in favour of **user choice** to install orchestrator on their app
- Distribution: **pip**, **npm**, **Windows PowerShell**, bash bootstrap

## Anti-pattern

- Do not merge draft PR **#117** as-is (hard-deletes wave scripts; conflicts with #116)
- Do not report installer/Windows/cease-wave as unfinished work after #116

## Session-start

Always run `python3 scripts/session-vault-brief.py` so installer truths in the vault are loaded before planning. Branch pointer alone is insufficient.
