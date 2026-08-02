# TODO — App-installable orchestrator + drop wave (2026-07-17)

**Branch:** `feature/app-installable-drop-wave-2026-07-17`  
**Plan:** `docs/internal/APP-INSTALLABLE-AND-DROP-WAVE-PLAN.md`  
**Base:** master v1.8.4  

## Priority

1. [x] **Uninstall** host + project (`orchestrator uninstall`, scripts/uninstall.sh|.ps1); CI stamp fix  
2. [x] **Inventory wave paths** still on tree; map to stop-wave branch deletions  
3. [x] **Phase A:** Delete fleet wave tooling + `orchestrator wave`; tests that they stay gone (`tests/test_wave_absent.py`)
4. [ ] **Freemium freeze:** define Light deploy selections + £99 = seat vs company (see FREEMIUM plan)  
5. [ ] **License server MVP** on DigitalOcean (`POST /api/licenses/validate` — already in CLI)  
6. [ ] **Phase B:** CI publish npm + pip (or GH Packages) on `v*` tags  
7. [x] **Phase C (local):** Remote GitHub version probe + `upgrade --if-available` + session `--offer`/`--prompt` (feature/orchestrator-check-upgrade-local-2026-07-18)
8. [ ] **Phase D:** Cherry-pick `vscode-extension` from `feature/vscode-extension-marketplace-2026-07-14`  
9. [ ] **Phase E:** PowerShell + bash “install CLI from registry” without monorepo clone  
10. [ ] Stripe £99 one-off → issue key → email  
11. [ ] Docs: registry-first install + buy Pro; remove wave from operator guides  
12. [ ] Pre-release gate green; PR → develop  


## Licensing plan

- Full write-up: `docs/internal/FREEMIUM-LICENSE-AND-SERVER-PLAN.md`  
- Reuse: `licensing_policy.py` (TRIAL_LITE / PRO_FULL), `license_server.py`, `docs/reference/licensing.md`  


## Reuse from older branches

| Branch | Use |
|--------|-----|
| `feature/stop-wave-autodeploy-installer-2026-07-08` | Wave hard-delete + install.ps1/sh/npm patterns |
| `feature/vscode-extension-marketplace-2026-07-14` | VS Code extension scaffold |

## Standing rules

- **No fleet wave** — delete, do not re-enable with env var  
- Per-app only: `orchestrator init|upgrade|check`  
- Do not publish `docs/internal/` to npm  
