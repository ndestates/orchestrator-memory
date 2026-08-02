# Production ship — host install (npm, pip, VS Code)

[UPDATED 2026-08-01] · **Apache-2.0 freeware** · product **2.2.0** · optional [Patreon](https://www.patreon.com/ndestates)

How **end users** install the orchestrator in production, and how **maintainers** publish a release.

There are **three host surfaces** (all free open source). There is **no Packagist** path (that is PHP/Composer — see FAQ below).

| Surface | Package / artifact | What users run |
|---------|-------------------|----------------|
| **Python host CLI** | PyPI `orchestrator` *or* GitHub Release wheel | `orchestrator …` · `orchestrator memory …` |
| **npm wrapper** | `@ndestates/orchestrator` | `npm i -g @ndestates/orchestrator` → installs Python CLI |
| **VS Code / Cursor** | Extension `ndestates.orchestrator-memory` (VSIX / Marketplace) | Palette commands → host CLI |

In-app template (`orchestrator init/upgrade`) is **optional** and separate from host install.

---

## A. Users — install in production (any machine)

### 1) Preferred: uv tool (Python)

```bash
# From GitHub Release wheel (no full clone required once published)
uv tool install \
  "orchestrator @ https://github.com/ndestates/orchestrator/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"

# Or when PyPI publish is enabled:
# uv tool install orchestrator==2.2.0

orchestrator version
orchestrator memory brief --seed
```

Ensure `~/.local/bin` (or uv’s tool bin) is on `PATH`.

### 2) pip

```bash
pip install \
  "https://github.com/ndestates/orchestrator/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"
# or: pip install orchestrator==2.2.0   # after PyPI
```

### 3) npm / pnpm via **GitHub Packages** (recommended Node path)

Package: **`@ndestates/orchestrator`** on **https://npm.pkg.github.com**  
(Published automatically on each `v*` release with `GITHUB_TOKEN` — no npmjs.org token required.)

```bash
# Auth once (GitHub PAT with read:packages, or GITHUB_TOKEN in CI)
# Create classic PAT: https://github.com/settings/tokens → read:packages
export NODE_AUTH_TOKEN=ghp_your_token_here   # or use ~/.npmrc below

# Project or user ~/.npmrc:
cat >> ~/.npmrc <<'EOF'
@ndestates:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
EOF

npm install -g @ndestates/orchestrator
# or: pnpm add -g @ndestates/orchestrator

orchestrator version
```

Postinstall installs/refreshes the **Python** package. Requires Python 3.10+ on the machine.

**Optional public npmjs.org:** only if repo secret `NPM_TOKEN` is set on release  
(`npm install -g @ndestates/orchestrator` from registry.npmjs.org).

### 4) From a git checkout (ops / maintainers)

```bash
git clone https://github.com/ndestates/orchestrator.git
cd orchestrator
git checkout v2.2.0   # or master after release

bash scripts/install.sh --uv-tool          # preferred host CLI
# bash scripts/install.sh --npm            # Node wrapper
# bash scripts/install.sh --cli --host-tools --mcp

orchestrator version
orchestrator memory status
```

Windows: `.\scripts\install.ps1 -Cli` / `-Npm`.

### 5) VS Code / Cursor extension

**End-user SSOT (all channels + every command):**  
[extensions/vscode-orchestrator/README.md](../../extensions/vscode-orchestrator/README.md)

Order: **host CLI first** (§1 in that README), then extension.

```bash
# Marketplace (when published)
code --install-extension ndestates.orchestrator-memory

# VSIX from GitHub Release or local package
code --install-extension /path/to/orchestrator-memory-2.1.0.vsix
```

Palette: Read instructions · Command Hub · Memory + vault storage · Brief · Query · Ingest · Seed · Status · Serve · Run /chain · skills  
Setting: `orchestrator.cliPath` (default `orchestrator` on PATH).  
**SemVer:** extension **2.2.0** is a **MINOR** (features); ship with product `VERSION` **2.2.0**.

### 6) Optional: template into one app repo

```bash
orchestrator init /path/to/app --from-github v2.2.0 --yes --no-pr
orchestrator upgrade /path/to/app --from-github v2.2.0 --yes --no-pr --quiet
```

Not required for `orchestrator memory` alone.

---

## B. Maintainers — ship a production release

### Preconditions

1. Feature work merged to **`master`** (or release branch you tag from).  
2. `VERSION` / stamp / `package.json` aligned: `python3 scripts/check-version-alignment.py`  
3. Pre-release gate green: `bash scripts/pre-release-gate.sh`  
4. License: **Apache-2.0** (`LICENSE`, `NOTICE`)  
5. Repo secrets (optional channels — skip cleanly if unset):

| Secret | Used for |
|--------|----------|
| `GITHUB_TOKEN` | Automatic — GitHub Release + **GitHub Packages npm** (`packages: write`) |
| `PYPI_API_TOKEN` | Optional — `twine upload` → PyPI |
| `NPM_TOKEN` | Optional — also publish to **npmjs.org** |
| `VSCE_PAT` | **Legacy optional** — CLI `vsce publish` only; prefer Marketplace manage UI |

GitHub Packages publish does **not** need a separate secret beyond default Actions permissions.

### Release steps (production)

```bash
# 1. On clean master (example)
git checkout master
git pull --ff-only
# ensure VERSION is 2.0.0 and features merged

# 2. Tag (triggers .github/workflows/release.yml)
git tag -a v2.2.0 -m "Release v2.2.0"
git push origin v2.2.0

# Or: Actions → Release → Run workflow → version=2.0.0 target=master
```

### What `release.yml` does on `v*` tags

1. Gate: VERSION == tag, stamp, package.json  
2. Gate: `pre-release-gate.sh` (tests + security)  
3. Create/update **GitHub Release** + notes  
4. **Build** wheel + sdist + SHA256SUMS + bundle-hashes  
5. **Attach** artifacts to the release  
6. **PyPI** publish if `PYPI_API_TOKEN` set  
7. **npm** publish if `NPM_TOKEN` set  
8. **VSIX** package + attach to Release; **Marketplace** = human upload on manage (same as vscode-grok4). Optional PAT publish only if you explicitly opt in

### Verify after ship

```bash
# GitHub assets
gh release view v2.2.0

# Host CLI from wheel URL
uv tool install --force "orchestrator @ https://github.com/ndestates/orchestrator/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"
orchestrator version
orchestrator memory status

# npm (if secret was set)
npm view @ndestates/orchestrator version

# PyPI (if secret was set)
pip index versions orchestrator   # or: pip install orchestrator==2.2.0
```

### PyPI package name note

`pyproject.toml` uses name `orchestrator`. If that name is taken or blocked on PyPI, rename before first publish (e.g. `ndestates-orchestrator`) and update postinstall + docs. GitHub Release wheels always work without PyPI.

### npm registries

| Registry | Package | When |
|----------|---------|------|
| **GitHub Packages** | `@ndestates/orchestrator` | Every `v*` release (default) |
| **npmjs.org** | `@ndestates/orchestrator` | Only if `NPM_TOKEN` set |

Install from GitHub Packages needs a PAT with `read:packages` (and SSO authorize for the org if required).

---

## C. Mental model (production)

```text
┌────────────────── users ──────────────────┐
│  uv / pip wheel    npm -g    VS Code VSIX │
└─────────┬───────────┬───────────┬─────────┘
          │           │           │
          ▼           ▼           ▼
     orchestrator CLI (Python) ◄── extension shells out
          │
          ├─ memory (any project)
          ├─ version / self-upgrade
          └─ optional init/upgrade into app repos
```

| Do | Don’t |
|----|--------|
| Ship **host package** first | Require every app to re-deploy skills for memory |
| Tag `vX.Y.Z` from master | Tag from a dirty feature branch |
| Attach wheels to GitHub Release | Rely only on unreleased feature branches |
| Treat VS Code as thin client | Embed full template in the extension |

---

## D. Current status (honest)

| Channel | Status |
|---------|--------|
| GitHub Release pipeline | **Ready** — builds wheel + sdist + VSIX on `v*` tags |
| Product version | **2.2.0** (`VERSION` / stamp / npm / extension) |
| Tag `v2.2.0` | Cut after pre-release gate on merge target (`master` / release branch) |
| Wheel URL | `…/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl` |
| Slash registration | `python3 scripts/register-all-slash-commands.py` (all hosts) |
| PyPI / npm secrets | Optional — publish only if secrets configured |
| VS Code Marketplace | **VSIX package + manage UI** (publisher `ndestates`, product **Visual Studio Code**). CI never requires `VSCE_PAT`. |

### VS Code extension ship path (Orchestrator Memory — AI token cache)

| Step | Who | How |
|------|-----|-----|
| 1. Package | CI / local | `vsce package` in `extensions/vscode-orchestrator/` or workflow **VS Code Marketplace** (package-only) |
| 2. Publish | Human | [manage/publishers/ndestates](https://marketplace.visualstudio.com/manage/publishers/ndestates) → **Visual Studio Code** → upload `orchestrator-memory-*.vsix` |
| 3. Install | User | Marketplace search **Orchestrator Memory** or `code --install-extension …vsix` |

**Do not** put Azure DevOps PATs in GitHub for day-to-day ship (global PATs retire **1 Dec 2026**). PAT/`vsce publish` remains opt-in legacy only.

Current extension version in tree: see `extensions/vscode-orchestrator/package.json` (**2.2.0** — semver MINOR with product `VERSION`).

**To ship host + extension to production:** merge feature work → master → tag `vX.Y.Z` → confirm Actions release job green → point users at the wheel URL (and npm/PyPI if secrets set) → upload latest VSIX on manage.

Workflow: `.github/workflows/vscode-marketplace.yml` (default **package-only**).

---

## FAQ — Why not Packagist?

[Packagist](https://packagist.org/) is the registry for **PHP Composer** packages (`composer require …`). This product’s runtime is:

| Stack | Registry |
|-------|----------|
| **Python CLI** | PyPI / GitHub Release wheels / `uv tool` |
| **Node wrapper** | npm (`@ndestates/orchestrator`) |
| **Editor** | VS Code Marketplace / VSIX |

Publishing to Packagist would only make sense for a **thin PHP shim** that shells out to the Python CLI — extra packaging, two version clocks, and almost no benefit for Laravel apps that already install the **host** tool with uv/npm. App code stays PHP; **the orchestrator is not a PHP library**.

---

## Related

- [Installation](../getting-started/installation.md)  
- [Host-first memory](host-first-memory.md)  
- [Licensing (freeware + Patreon)](../reference/licensing.md)  
- [Versioning](../reference/versioning.md)  
- Extension: `extensions/vscode-orchestrator/README.md`  
- Workflow: `.github/workflows/release.yml`
