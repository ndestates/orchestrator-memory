# Public product vs private factory

| Repo | Visibility | Purpose |
|------|------------|---------|
| [ndestates/orchestrator-memory](https://github.com/ndestates/orchestrator-memory) | **Public** | Product people install: CLI wheel, VSIX, release tags, product docs |
| [ndestates/orchestrator](https://github.com/ndestates/orchestrator) | **Private** | Full orchestrator factory: all branches, template, internal work |

**BYOK:** Users must use **their own** model-provider accounts and API keys.  
See [Bring your own keys](bring-your-own-keys.md).

## Install (public)

```bash
VER=2.2.0
uv tool install --force \
  "orchestrator @ https://github.com/ndestates/orchestrator-memory/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"
```

## Develop (private)

Clone `ndestates/orchestrator` (private). Remotes on a maintainer machine:

```text
origin  → ndestates/orchestrator          (private factory)
public  → ndestates/orchestrator-memory   (public product; publish carefully)
```

Publish product snapshots to `public` as clean trees (orphan or release branch) — do not push full lab history if secret scanning blocks it.
