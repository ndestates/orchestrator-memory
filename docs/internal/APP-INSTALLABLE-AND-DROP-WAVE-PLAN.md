# Plan: App-installable orchestrator + drop fleet wave forever

**Branch:** `feature/app-installable-drop-wave-2026-07-17`  
**Base:** `master` @ v1.8.4  
**Status:** Phase A implemented 2026-07-18 (wave tooling deleted); Phases B–F open
**Classification:** Internal engineering plan (also kept under `docs/internal/` — not product marketing)

---

## 1. Goal

Make **every app** able to:

1. **Detect** whether orchestrator is installed and which version  
2. **Fetch** a released version without a monorepo checkout  
3. **Install / upgrade** the template into the app (per-app only)  
4. Do this via **npm**, **pip (PyPI)**, **PowerShell**, and **VS Code extension**  
5. **Never** use multi-app fleet wave deploy again  

Wave becomes **deleted**, not merely blocked by env var.

---

## 2. What already exists (v1.8.4)

| Surface | State | Gap |
|---------|--------|-----|
| **Python CLI** `orchestrator_cli` | `init`, `upgrade`, `check`, `status`, `version`, license | Not reliably published to **PyPI** on each tag |
| **npm** `@ndestates/orchestrator` | Thin Node wrapper + postinstall → pip | Package may not be **published to npmjs** on each release; `files` is thin (OK) |
| **install.sh / install.ps1** | Bootstrap this repo; `-Cli` / `-Npm` | Oriented at **template checkout**, not “app downloads release” |
| **session-orchestrator-check.py** | In-app version announce without full CLI | Depends on lock + stamp; needs published version as source of truth |
| **per-app-upgrade.md** | Documents upgrade path | Still assumes operator often has git checkout of orchestrator |
| **Wave scripts** | Still in repo; CLI `wave` blocked unless env override | Must **remove** entirely |
| **VS Code extension** | Scaffold on `feature/vscode-extension-marketplace-2026-07-14` only | Not on master; not published to Marketplace |
| **Release workflow** | Tags + GitHub Release artifacts | Need explicit **npm publish + PyPI publish + vsce publish** jobs |

---

## 3. Older branches that already explored this

| Branch | What it did | Reuse? |
|--------|-------------|--------|
| **`feature/stop-wave-autodeploy-installer-2026-07-08`** | **Hard-delete** fleet wave scripts (~29 paths); install.sh/ps1; npm postinstall; licensing_policy; Ollama host-only; removed `wave` CLI | **Primary source** for wave removal + install polish (cherry-pick carefully; diverged from later 1.8.x) |
| **`feature/vscode-extension-marketplace-2026-07-14`** | Full `vscode-extension/` (package.json, extension.js, README); Command Palette → version/status/check/init/upgrade | **Cherry-pick onto this branch** as baseline extension |
| **`feature/installer-cli-phase2`** | Name misleading in history — later became Didit/Loqate vendor skills, not pure installer | **Skip** for this initiative |
| **`feature/restore-ollama-install-1.8.1`** | Ollama BYOM restore | Unrelated except install.ps1 patterns |
| **#116 / #117 PR hygiene** (reports) | Product decision: #116 fail-closed wave vs #117 hard-delete wave | This plan **chooses hard-delete** (never seen again) |
| **docs/guides/per-app-upgrade.md** | Current operator path | Evolve into “install from registry” guide |

### Useful commits (investigate when implementing)

```text
feature/stop-wave-autodeploy-installer-2026-07-08
  c5aae47 refactor: remove fleet wave tooling; Ollama host-only BYOM
  b6473b4 feat(install): cross-platform installer, licensing policy, …

feature/vscode-extension-marketplace-2026-07-14
  a020ca4 feat(vscode): marketplace extension wrapping orchestrator npm/CLI
```

---

## 4. Target architecture (apps install themselves)

```text
                    ┌──────────────────────────────┐
                    │  GitHub Release vX.Y.Z       │
                    │  + source + wheels + notes   │
                    └───────────┬──────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   npmjs.org              PyPI / GitHub          VS Marketplace
 @ndestates/              wheel: orchestrator    "Orchestrator"
 orchestrator             (hatchling)            (thin UI)
          │                     │                     │
          └──────────┬──────────┘                     │
                     ▼                                │
              orchestrator CLI  ◄─────────────────────┘
                     │
                     ├── check / status / version
                     ├── init <app>
                     └── upgrade <app>  (+ --verify-bundle)
```

**App-local loop (no wave inventory):**

```bash
# anywhere with network
npm install -g @ndestates/orchestrator@latest
# or: pip install -U orchestrator==1.8.4
# or: .\Install-Orchestrator.ps1 -Version 1.8.4

cd /path/to/app
orchestrator check .
orchestrator upgrade . --no-pr
```

Session-start continues to run `session-orchestrator-check.py` and surface “upgrade available”.

---

## 5. Workstreams (implementation order)

### Phase A — Kill wave (never again)

1. Delete fleet wave scripts and inventory (list from stop-wave branch + current tree):
   - `scripts/deploy-*-wave.sh`, `scripts/wave-*.sh`, `wave-inventory.yaml`, fleet compound scripts, etc.
2. Remove `orchestrator wave` command and tests that only exist for wave.
3. Update docs: installation, template-deploy, per-app-upgrade — **no wave override**.
4. Guard: any remaining path matching `*-wave*` in scripts/ fails a new unit test or malware-style allowlist.
5. CHANGELOG: “Fleet wave deploy removed permanently.”

### Phase B — Publishable packages (source of truth = VERSION)

1. **PyPI (or GitHub Packages first)**  
   - Release workflow: `python -m build` → upload wheel/sdist on tag `v*`  
   - Name: confirm `orchestrator` on PyPI availability; if taken, `ndestates-orchestrator` / `orchestrator-cli`  
2. **npm**  
   - On tag: `npm publish` for `@ndestates/orchestrator` (auth via OIDC or token secret)  
   - postinstall: prefer `pip install orchestrator==$VERSION` from PyPI; fallback GitHub release wheel URL  
3. **PowerShell app installer**  
   - New `scripts/Install-Orchestrator.ps1` (or improve `install.ps1`) that:
     - Installs CLI from npm **or** pip for a given `-Version`
     - Does **not** require cloning the monorepo  
4. **Bash app installer**  
   - Symmetric: `scripts/install-orchestrator-cli.sh --version 1.8.4`  
5. Version single source: `/VERSION` → package.json / pyproject / vscode-extension package.json via sync script in CI  

### Phase C — In-app check & download

1. Strengthen `orchestrator check` / `update_check.py`:
   - Query **published** version (npm registry or PyPI JSON or GitHub Releases API), not only local template checkout  
2. `session-orchestrator-check.py` uses same remote version endpoint when network allowed  
3. Document offline mode (`ORCHESTRATOR_NO_UPDATE_CHECK=1`, pin lock)  

### Phase D — VS Code / Cursor extension

1. Cherry-pick `vscode-extension/` from marketplace branch  
2. Bump extension version with monorepo VERSION  
3. Publish via `vsce` / `ovsx` in release workflow (secrets: marketplace PAT)  
4. Commands: version, check, upgrade only (no wave)  

### Phase E — Release pipeline

Extend `.github/workflows/release.yml` (after pre-release-gate):

| Job | Artifact |
|-----|----------|
| gate | existing pre-release-gate |
| pypi | wheel + sdist publish |
| npm | `@ndestates/orchestrator` publish |
| vscode | VSIX + marketplace publish (optional flag) |
| github-release | attach wheels + vsix |

### Phase F — App docs & deprecation

1. Rewrite `docs/getting-started/installation.md` and `per-app-upgrade.md` for registry-first  
2. Remove wave sections from skills/copilot-instructions  
3. One migration note: “wave scripts gone; use orchestrator upgrade”  

---

## 6. Non-goals (this initiative)

- Reintroducing multi-app unattended deploy  
- Publishing `docs/internal/`  
- Changing app business domain code  

---

## 7. Acceptance criteria

- [x] No `scripts/*wave*` fleet deploy entrypoints remain (except historical docs/changelog mentions)  
- [x] `orchestrator wave` command removed  
- [x] On tag `vX.Y.Z`, CI publishes **npm** and **pip** packages with matching version (when `NPM_TOKEN` / `PYPI_API_TOKEN` set)  
- [ ] From a clean machine (no monorepo): install CLI → `orchestrator upgrade ./app` works  
- [ ] PowerShell one-liner / script documented for Windows apps  
- [ ] VS Code extension on branch and publish path documented (or published)  
- [ ] Session-start still announces upgrade when behind published version  
- [ ] Tests cover: version check remote mock, wave scripts absent, install scripts smoke  

---

## 8. Risks & decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| PyPI project name | `orchestrator` vs scoped name | Check availability; prefer clear ND Estates ownership |
| Private vs public npm | npmjs public vs GitHub Packages | Public if product is open enough; GH Packages if private |
| Wave delete vs archive | Delete vs `archive/wave/` | **Delete** from mainline; history remains in git |
| Extension publisher | `ndestates` | Confirm Marketplace publisher account |

---

## 9. Immediate next steps on this branch

1. Inventory wave file list (script) and open deletion PR-sized commits  
2. Cherry-pick vscode-extension scaffold  
3. Design release.yml publish jobs (secrets checklist)  
4. Prototype remote version check against GitHub Releases API (no auth)  
5. Align INSTALL.md + per-app-upgrade to registry-first  

---

## 10. Wave paths still present on master (v1.8.4) — delete list

```text
scripts/backfill-wave-vault.sh
scripts/commit-cache-efficiency-wave.sh
scripts/commit-template-wave-skip.sh
scripts/commit-template-wave.sh
scripts/commit-token-meter-wave.sh
scripts/deploy-cache-efficiency-wave.sh
scripts/deploy-loops-starter-wave.sh
scripts/deploy-mcp-wave.sh
scripts/deploy-registry-wave.py
scripts/deploy-session-start-wave.sh
scripts/deploy-skills-customize-wave.sh
scripts/deploy-template-wave-skip.sh
scripts/deploy-template-wave.sh
scripts/deploy-token-meter-wave.sh
scripts/fix-chain-audit-wave.sh
scripts/fix-node24-wave.sh
scripts/resolve-wave-app-path.py
scripts/wave-app-branch.sh
scripts/wave-app-prepare-branch.sh
scripts/wave-apps.sh
scripts/wave-deploy-guard.sh
scripts/wave-deploy-policy.sh
scripts/wave-inventory.yaml
src/orchestrator_cli/commands/wave.py
tests/test_wave_app_prepare_branch.py
tests/test_wave_deploy_policy.py
```

Also grep for `fleet_compound`, `wave-apps`, `ORCHESTRATOR_WAVE_DEPLOY_APPROVED` in skills/docs and remove or rewrite.

## 11. Related links

- Current install: `INSTALL.md`, `docs/getting-started/installation.md`  
- Per-app: `docs/guides/per-app-upgrade.md`  
- CLI: `src/orchestrator_cli/`  
- npm: `package.json`, `scripts/npm/postinstall.js`  
- Release: `.github/workflows/release.yml`  
- Security/internal map: `docs/internal/SECURITY-POSTURE.md`, `CODEBASE-MAP.md`  
