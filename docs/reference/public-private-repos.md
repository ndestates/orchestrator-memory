# Public product vs private factory

[UPDATED 2026-09-17] — product **3.0.0** · npm-only user install

| Repo | Visibility | Purpose |
|------|------------|---------|
| [ndestates/orchestrator-memory](https://github.com/ndestates/orchestrator-memory) | **Public** | Product people install: npm package metadata, CLI wheel, VSIX, release tags, product docs |
| [ndestates/orchestrator](https://github.com/ndestates/orchestrator) | **Private** | Full orchestrator factory: all branches, template, internal work |

**BYOK:** Users must use **their own** model-provider accounts and API keys.  
See [Bring your own keys](bring-your-own-keys.md).

## Install (public)

```bash
npm install -g @ndestates/orchestrator
orchestrator version
```

The npm shim expects a GitHub Release **wheel at the same version** on this public repo:

`https://github.com/ndestates/orchestrator-memory/releases/download/v3.0.0/orchestrator-3.0.0-py3-none-any.whl`

Do not publish an npm version without attaching that matching wheel.

## Develop (private)

Clone `ndestates/orchestrator` (private). Remotes on a maintainer machine:

```text
origin  → ndestates/orchestrator          (private factory)
public  → ndestates/orchestrator-memory   (public product; publish carefully)
```

Override upgrade/release probes only when you mean to hit the factory:

```bash
export ORCHESTRATOR_GITHUB_REPO=ndestates/orchestrator
```

Default (unset) is `ndestates/orchestrator-memory`.

Publish product snapshots to `public` as clean trees (orphan or release branch) — do not push full lab history if secret scanning blocks it.
