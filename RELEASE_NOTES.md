# Release notes — v2.2.0

**Date:** 2026-08-02  
**Tag:** `v2.2.0`  
**Previous public tag:** `v2.0.0` (2.1.0 existed in tree but was never published as a GitHub Release)

## Highlights

1. **Host CLI wheel + sdist** on GitHub Release (install without cloning)
2. **Multi-surface slash commands** — every skill registered for Grok · Claude · Cursor · Copilot · Gemini · ChatGPT
3. **VS Code / Cursor extension 2.2.0** — real `/chain session-start` in palette + Chat; one-click setup
4. **Canonical session opener** remains: `/chain session-start`

## Install host CLI (wheel)

```bash
VER=2.2.0
uv tool install --force \
  "orchestrator @ https://github.com/ndestates/orchestrator/releases/download/v${VER}/orchestrator-${VER}-py3-none-any.whl"

orchestrator version          # → 2.2.0
orchestrator memory brief --seed
```

Or pip:

```bash
pip install --upgrade \
  "https://github.com/ndestates/orchestrator/releases/download/v2.2.0/orchestrator-2.2.0-py3-none-any.whl"
```

## Slash commands (all models)

```bash
# After adding skills under .grok/skills/:
python3 scripts/register-all-slash-commands.py
python3 scripts/register-all-slash-commands.py --check
```

| Host | Example |
|------|---------|
| Grok | `/chain session-start` · `/always-on-memory` |
| Claude Code | `/chain session-start` · `/code-review` |
| Cursor | `/chain` · skills under `.cursor/commands/` |
| Catalog | `docs/reference/slash-commands.md` |

## VS Code / Cursor extension

- Item: `ndestates.orchestrator-memory` **2.2.0**
- VSIX asset: `orchestrator-memory-2.2.0.vsix`
- Palette: type `/chain session-start` · Chat: `@orchestrator /session-start`

```bash
code --install-extension path/to/orchestrator-memory-2.2.0.vsix
```

## Release artifacts (this tag)

| Asset | Purpose |
|-------|---------|
| `orchestrator-2.2.0-py3-none-any.whl` | Host CLI (uv/pip) |
| `orchestrator-2.2.0.tar.gz` | sdist |
| `orchestrator-memory-2.2.0.vsix` | VS Code / Cursor extension |
| `SHA256SUMS.txt` | Checksums |
| `bundle-hashes.json` | Security bundle stamp |

## Before tagging

```bash
bash scripts/pre-release-gate.sh   # MUST PASS
python3 scripts/check-version-alignment.py
```

## Ship

```bash
# After merge to master (or chosen release branch):
git tag -a v2.2.0 -m "Release v2.2.0"
git push origin v2.2.0
# → .github/workflows/release.yml builds + attaches wheel/sdist/VSIX
```

## Compare

https://github.com/ndestates/orchestrator/compare/v2.0.0...v2.2.0

## Docs

- [Installation](docs/getting-started/installation.md)
- [Production ship](docs/guides/production-ship.md)
- [Platform surfaces](docs/reference/platform-surfaces.md)
- [Slash catalog](docs/reference/slash-commands.md)
