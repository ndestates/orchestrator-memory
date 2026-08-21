# Production ship — host install (npm, pip, VS Code)


> **Repository split (2026-08-02)**  
> | Repo | Visibility | Role |  
> |------|------------|------|  
> | **[ndestates/orchestrator-memory](https://github.com/ndestates/orchestrator-memory)** | **Public** | Product: host CLI wheel, VSIX, install docs, release tags |  
> | **[ndestates/orchestrator](https://github.com/ndestates/orchestrator)** | **Private** | Factory: full template, `develop` / feature branches, internal work |  
>
> End users install from **orchestrator-memory** releases only. Maintainers develop on **orchestrator** (private).

[UPDATED 2026-08-01] · **Apache-2.0 freeware** · product **2.2.0** · optional [Patreon](https://www.patreon.com/ndestates)

How **end users** install the orchestrator in production, and how **maintainers** publish a release.

### Bring your own keys (required)

This product is **not** a cloud model API. **You** must have:

- Accounts with the AI tools you use (Claude, Grok/xAI, Copilot, Cursor, Gemini, ChatGPT/OpenAI, …), and  
- **Your own** API keys when you call a provider API (env vars / host settings — never committed to git).

We do **not** issue or embed OpenAI, Anthropic, xAI, Google, or other vendor keys.  
Full policy: [Bring your own keys](../reference/bring-your-own-keys.md).

There is **no Packagist** path (that is PHP/Composer — see FAQ below).

| Surface | Package / artifact | What users run |
|---------|-------------------|----------------|
| **npm (only)** | `@ndestates/orchestrator` on **npmjs** | `npm install -g @ndestates/orchestrator` |
| **VSIX / Marketplace / uv / pip / fleet** | **Not product install paths** | Do not document |

In-app template (`init`/`upgrade`) is **explicit** and separate. Existing app repos are not rewritten until someone runs upgrade. Publish npm + wheel from **orchestrator-memory**, not this factory.

---

## A. Users — install in production (any machine)

### 1) Only: npm install (npmjs)

```bash
npm install -g @ndestates/orchestrator
orchestrator version
orchestrator memory brief --seed
npx orchestrator init /path/to/app --no-pr   # files; explicit
```

Requires Python 3.10+. If `import orchestrator_cli` fails:

```bash
python3 -m pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v2.3.0/orchestrator-2.3.0-py3-none-any.whl"
```

### 2) Advanced / maintainer: uv tool (Python)

```bash
# From GitHub Release wheel (no full clone required once published)
uv tool install \
  "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"

# Or when PyPI publish is enabled:
# uv tool install orchestrator==2.2.0

orchestrator version
orchestrator memory brief --seed
```

Ensure `~/.local/bin` (or uv’s tool bin) is on `PATH`.

### 3) pip (same wheel; PATH install)

```bash
pip install \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"
# or: pip install orchestrator==2.2.0   # after PyPI
```

### 4) GitHub Packages (legacy Node registry — not the user path)

User npx resolves on **npmjs**. GitHub Packages is no longer the documented install. Maintainers may still have old `~/.npmrc` entries; remove `@ndestates:registry=https://npm.pkg.github.com` so `npx` hits npmjs.

### 5) From a git checkout (ops / maintainers)

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

### 6) VS Code / Cursor extension — **parked**

Not a user install path. Existing VSIX installs may still call the host CLI. Do not publish Marketplace updates as the install story. Use the IDE terminal + npx.

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

### What release workflows do on `v*` tags

| Workflow | Repo | Gate |
|----------|------|------|
| **`release.yml`** | Private **`ndestates/orchestrator`** only | Full `pre-release-gate.sh` (pytest + security) |
| **`product-release.yml`** | Public **`ndestates/orchestrator-memory`** only | VERSION/stamp only — **no** factory suite |

**Product release (`product-release.yml`) steps:**

1. Gate: VERSION == tag (+ stamp + package.json)  
2. Create/update **GitHub Release** + notes  
3. **Build** wheel + sdist + SHA256SUMS (+ bundle-hashes if present)  
4. **Attach** artifacts  
5. **npm** GitHub Packages (optional npmjs/PyPI with secrets)  
6. **VSIX** package + attach; Marketplace if `VSCE_PAT` set

### Verify after ship

```bash
# GitHub assets
gh release view v2.2.0

# Host CLI from wheel URL
uv tool install --force "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"
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
