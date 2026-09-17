# Release notes — v3.0.0

**Date:** 2026-09-17  
**Tag:** `v3.0.0` (cut after merge — see human steps below)  
**Previous public tag:** `v2.3.5` (npm later reached **2.3.10** without a matching wheel)

## Why 3.0.0

The public product line moves to **3.x**. Do not keep patching 2.3.x as current.

2.3.x shipped a real user-facing break: `@ndestates/orchestrator@2.3.10` on npm requested `v2.3.10` of `orchestrator-2.3.10-py3-none-any.whl`, but GitHub Releases on this repo only published wheels through **v2.3.5**. That URL 404’d.

## Highlights

1. **One user install method:** `npm install -g @ndestates/orchestrator`
2. **Public repo is the product face** — clone, Release, and upgrade URLs default to `ndestates/orchestrator-memory`
3. **Matching artifacts required** — npm `X.Y.Z` and GitHub Release wheel `orchestrator-X.Y.Z-py3-none-any.whl` ship together
4. uv / pip / `install.sh` / private factory clone quarantined under Maintainer / Private
5. `.github/workflows/product-release.yml` builds and attaches the wheel on `v*` tags

## Install (users)

```bash
npm install -g @ndestates/orchestrator
orchestrator version          # → 3.0.0 after this release is published
orchestrator memory brief --seed
```

If the Python module is missing, install the **same-version** wheel from:

`https://github.com/ndestates/orchestrator-memory/releases/download/v3.0.0/orchestrator-3.0.0-py3-none-any.whl`

## Before tagging

```bash
python3 scripts/check-version-alignment.py
python3 scripts/check-release-wheel.py --local
```

## Human publish steps (this tree cannot npm-publish or cut the Release without your token)

1. Merge this branch to `master`.
2. Tag `v3.0.0` on **ndestates/orchestrator-memory** and push the tag.
3. Confirm Actions **Product release** attached `orchestrator-3.0.0-py3-none-any.whl`.
4. Only then publish npm `3.0.0` (workflow does this when `NPM_TOKEN` is set; otherwise `npm publish --access public` locally).
5. Verify:

   ```bash
   npm view @ndestates/orchestrator version    # 3.0.0
   python3 scripts/check-release-wheel.py --remote
   ```

Do **not** publish npm 3.0.0 before the wheel exists.

## Compare

https://github.com/ndestates/orchestrator-memory/compare/v2.3.5...v3.0.0

## Docs

- [Installation](docs/getting-started/installation.md)
- [Production ship](docs/guides/production-ship.md)
- [Public vs private](docs/reference/public-private-repos.md)

## Historical

Release notes for **v2.2.0** (2026-08-02) documented the first public wheel train. That line is superseded.
