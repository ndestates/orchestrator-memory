# Production ship — matching npm + GitHub Release wheel

[UPDATED 2026-09-17] · **Apache-2.0 freeware** · product **3.0.0** · optional [Patreon](https://www.patreon.com/ndestates)

> **Repository split**  
> | Repo | Visibility | Role |  
> |------|------------|------|  
> | **[ndestates/orchestrator-memory](https://github.com/ndestates/orchestrator-memory)** | **Public** | Product: host CLI wheel, npm metadata, install docs, release tags |  
> | **[ndestates/orchestrator](https://github.com/ndestates/orchestrator)** | **Private** | Factory: full template, `develop` / feature branches, internal work |  
>
> End users install with **npm**. Maintainers develop on the private factory and publish **matching** artifacts here.

### Bring your own keys (required)

This product is **not** a cloud model API. **You** must have accounts with the AI tools you use and **your own** API keys when you call a provider API.  
Full policy: [Bring your own keys](../reference/bring-your-own-keys.md).

| Surface | Package / artifact | What users run |
|---------|-------------------|----------------|
| **npm (only)** | `@ndestates/orchestrator` on **npmjs** | `npm install -g @ndestates/orchestrator` |
| **GitHub Release wheel** | Same version as npm | Printed by the shim when `orchestrator_cli` is missing |
| **VSIX / Marketplace / uv / pip / fleet** | **Not product install paths** | Maintainer / parked |

`init`/`upgrade` is **explicit** and separate. Existing app repos are not rewritten until someone runs upgrade.

---

## A. Users — install in production

```bash
npm install -g @ndestates/orchestrator
orchestrator version
orchestrator memory brief --seed
npx orchestrator init /path/to/app --no-pr   # files; explicit
```

Requires Python 3.10+. If `import orchestrator_cli` fails, install the **matching** wheel:

```bash
VER=3.0.0
python3 -m pip install --upgrade \
  "https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
```

`VER` must equal the npm package version. A 404 means that Release was not published — do not mix npm 3.x with an older 2.x wheel.

uv / pip / clone / `install.sh` live under [Installation → Maintainer / private factory](../getting-started/installation.md#maintainer--private-factory).

---

## B. Maintainers — cut a matching 3.x release

**Rule:** never publish npm `X.Y.Z` without a GitHub Release `vX.Y.Z` that attaches `orchestrator-X.Y.Z-py3-none-any.whl`. That mismatch is what made npm 2.3.10 request a missing v2.3.10 wheel.

This public repo ships `.github/workflows/product-release.yml` (VERSION/stamp gate only — no factory pytest suite). The private factory may still have `release.yml` with the full `pre-release-gate.sh`.

### Preconditions

1. Feature work merged to **`master`** (or the branch you tag from).
2. Product identity is **3.x+** (`VERSION`, stamp, `package.json`, extension). Do not keep shipping 2.3.x as current.
3. `python3 scripts/check-version-alignment.py` is green.
4. `python3 scripts/check-release-wheel.py --local` is green (expected wheel name matches `VERSION`).
5. Optional secrets (skip cleanly if unset):

| Secret | Used for |
|--------|----------|
| `GITHUB_TOKEN` | Automatic — GitHub Release attach (`contents: write`) |
| `NPM_TOKEN` | Optional — publish `@ndestates/orchestrator` to npmjs |
| `PYPI_API_TOKEN` | Optional — PyPI (name `orchestrator` may be taken) |
| `VSCE_PAT` | Legacy optional Marketplace CLI publish |

### Release steps (this public repo)

```bash
# 1. On clean master
git checkout master
git pull --ff-only
python3 scripts/check-version-alignment.py   # VERSION == 3.0.0 (or next 3.x)

# 2. Tag — triggers product-release.yml
git tag -a v3.0.0 -m "Release v3.0.0"
git push origin v3.0.0

# Or: Actions → Product release → Run workflow → version=3.0.0
```

### What `product-release.yml` does on `v*` tags

1. Gate: `VERSION` == tag (and stamp / package.json / extension pin)
2. Build wheel + sdist + `SHA256SUMS.txt`
3. Create/update **GitHub Release** on **ndestates/orchestrator-memory** and attach artifacts
4. **npm publish** only if `NPM_TOKEN` is set; otherwise print the exact human npm command
5. Optional VSIX package when `vsce` is available (Marketplace upload stays a human step unless `VSCE_PAT` is set)

### Human steps if CI publish is blocked (no secrets)

Do these **in order** so npm never leads the wheel:

1. Confirm `VERSION` is the 3.x you intend (example **3.0.0**).
2. Merge this branch to `master`.
3. Tag and push `v3.0.0` on **ndestates/orchestrator-memory**.
4. Confirm Actions **Product release** built and attached `orchestrator-3.0.0-py3-none-any.whl`.
5. If the workflow could not publish npm:

   ```bash
   npm publish --access public
   npm view @ndestates/orchestrator version   # must print 3.0.0
   ```

6. Verify the wheel URL returns 200 (not 404):

   ```bash
   python3 scripts/check-release-wheel.py --remote
   curl -I "https://github.com/ndestates/orchestrator-memory/releases/download/v3.0.0/orchestrator-3.0.0-py3-none-any.whl"
   ```

7. Optional: upload `orchestrator-memory-3.0.0.vsix` via [Marketplace manage](https://marketplace.visualstudio.com/manage/publishers/ndestates).

**Do not** `npm publish` 3.0.0 (or any later 3.x) before the matching Release wheel exists.

### Verify after ship

```bash
gh release view v3.0.0 --repo ndestates/orchestrator-memory
npm view @ndestates/orchestrator version
npm install -g @ndestates/orchestrator@3.0.0
orchestrator version
```

### npm registries

| Registry | Package | When |
|----------|---------|------|
| **npmjs.org** | `@ndestates/orchestrator` | User path — only after the matching wheel is on the Release |
| **GitHub Packages** | `@ndestates/orchestrator` | Optional / legacy; not the documented install |

---

## C. Mental model (production)

```text
┌────────────────── users ──────────────────┐
│  npm install -g @ndestates/orchestrator   │
│  (shim → python -m orchestrator_cli)      │
│  missing module → matching Release wheel  │
└──────────────────┬────────────────────────┘
                   ▼
            orchestrator CLI (Python)
                   ├─ memory (any project)
                   ├─ version / self-upgrade
                   └─ optional init/upgrade into app repos
```

| Do | Don’t |
|----|--------|
| Ship **npm + wheel** at the same `X.Y.Z` | Publish npm without the GitHub wheel |
| Tag `vX.Y.Z` on **orchestrator-memory** | Point users at the private factory |
| Keep 3.x as the current line | Patch 2.3.x as current |

---

## D. Current status (honest)

| Channel | Status |
|---------|--------|
| Product version in this tree | **3.0.0** (`VERSION` / stamp / npm / extension) |
| Last published GitHub Release (before this cut) | **v2.3.5** wheel exists; npm **2.3.10** had no matching wheel |
| `product-release.yml` | In this public repo — builds wheel on `v*` tags |
| npm 3.0.0 | **Not published by this change** — human/CI with `NPM_TOKEN` |
| VS Code Marketplace | Optional; not the user install story |

---

## FAQ — Why not Packagist?

[Packagist](https://packagist.org/) is the registry for **PHP Composer** packages. This product’s runtime is Python + an npm shim. Publishing to Packagist would add a second version clock with no benefit.

---

## Related

- [Installation](../getting-started/installation.md)  
- [Public vs private repos](../reference/public-private-repos.md)  
- [Host-first memory](host-first-memory.md)  
- [Versioning](../reference/versioning.md)  
- Workflow: `.github/workflows/product-release.yml`
