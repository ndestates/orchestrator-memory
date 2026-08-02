# TODO — Freemium freeze + license server + publish (2026-07-18)

**Branch:** `feature/freemium-license-publish-2026-07-18`  
**Base:** merged develop #174 + master #173  
**Status:** **HELD** — PayPal production / go-live paused; do not unhold without ask. Multi-session **abandoned** for orchestrator (mailchimp only).  
**Plans:**
- `docs/internal/FREEMIUM-LICENSE-AND-SERVER-PLAN.md`
- `docs/internal/APP-INSTALLABLE-AND-DROP-WAVE-PLAN.md` (Phases B–E)

## Priority

1. [x] **Freemium freeze:** Light selections; **Pro £99/mo company** (annual 10× = 2 mo free) — `FREEMIUM-PRODUCT-FREEZE.md`
2. [x] **License server MVP** (code): validate + issue + revoke + SQLite + `services/license-api/` DO scaffold
3. [x] **Phase B:** release.yml publishes npm + pip on `v*` when secrets set
4. [ ] **Operator:** Deploy license-api to DigitalOcean; set `ORCHESTRATOR_LICENSE_ADMIN_TOKEN` + volume
5. [ ] **Operator:** Add GitHub secrets `PYPI_API_TOKEN` + `NPM_TOKEN` before next release tag
6. [ ] **Phase C:** Remote version check for `orchestrator check` / session-orchestrator-check (partially on develop via GitHub probe)
7. [ ] **Phase D:** Cherry-pick `vscode-extension` from `feature/vscode-extension-marketplace-2026-07-14`
8. [ ] **Phase E:** PowerShell + bash “install CLI from registry” without monorepo clone
9. [x] **PayPal on ndestates-io:** checkout + webhook + `/api/licenses/validate` (wire-ready; mock tests green)
10. [ ] Operator: live PayPal plan IDs + webhook URL on production ndestates.io
11. [ ] Email license key after purchase (SES/Mail)
10. [ ] Docs: registry-first install + buy Pro
11. [ ] Pre-release gate green; PR → develop

## Standing rules

- **No fleet wave** — deleted on develop (Phase A); never reintroduce
- Per-app only: `orchestrator init|upgrade|check`
- Do not publish `docs/internal/` to npm

## Done recently (parent)

- [x] Phase A: delete fleet wave tooling + `orchestrator wave` + absence tests (PR #172)
- [x] Uninstall CLI + CI stamp fix (prior)
