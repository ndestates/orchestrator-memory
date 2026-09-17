# VS Code Marketplace publishing (Orchestrator Memory)

Same process as **[vscode-grok4](https://github.com/ndestates/vscode-grok4)**  
(`grok-integration/docs/MARKETPLACE_PUBLISHING_GUIDE.md`).

Publisher: **`ndestates`** · Extension: **`ndestates.orchestrator-memory`**

## One-time setup (account)

1. Azure DevOps: https://dev.azure.com/ → create org if needed  
2. **PAT** → Custom scopes → **Marketplace: Acquire + Manage**  
3. Confirm publisher **`ndestates`** exists:  
   https://marketplace.visualstudio.com/manage  
4. Store PAT in GitHub:  
   ```bash
   gh secret set VSCE_PAT --repo ndestates/orchestrator-memory
   # paste Azure DevOps PAT (not a GitHub token)
   ```

## Publish automatically (recommended)

### On every version tag

```bash
# VERSION / package.json / extension package.json aligned (e.g. 3.0.0)
git tag -a v3.0.0 -m "Release v3.0.0"
git push origin v3.0.0
```

Runs:

- `.github/workflows/product-release.yml` — matching wheel + sdist on this public repo  
- Marketplace upload remains a human step unless `VSCE_PAT` is set  

### Manual marketplace-only

GitHub → **Actions** → **Product release** → **Run workflow** (wheel), then upload the VSIX on Marketplace manage.

- `version`: e.g. `3.0.0`

## Publish from your laptop (same as Grok)

```bash
cd extensions/vscode-orchestrator
npm install -g @vscode/vsce
vsce login ndestates          # paste Azure DevOps PAT
vsce package
vsce publish                  # or: vsce publish -p "$VSCE_PAT"
```

## Install after publish

```text
ext install ndestates.orchestrator-memory
```

Or Marketplace search: **Orchestrator Memory**.

Users still need host CLI: `orchestrator memory …` on PATH.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Value cannot be null. Parameter name: v1` | Icon ≥128×128 (we use 256×256); publisher id must be `ndestates`; full metadata present |
| `Publisher not found` | Create publisher `ndestates` on manage page |
| `401` | Use **Azure DevOps** PAT, not GitHub PAT |
| Version exists | Bump `version` in extension `package.json` |

## Local VSIX (before Marketplace)

```bash
# After package
code --install-extension ./orchestrator-memory-2.1.0.vsix
```
