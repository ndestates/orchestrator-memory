# Versioning (host · template · app)

[UPDATED 2026-08-04] — CLI + extension same VERSION; Marketplace next must exceed live

## Single source of truth

| Artifact | Role |
|----------|------|
| **`VERSION`** | **SSOT** — full product identity (`1.9.5` or `1.9.0-pre.5`) |
| `scripts/orchestrator-template-version` | Deployed stamp apps/session-check read |
| `package.json` `version` | npm wrapper (must match `VERSION`) |
| `extensions/vscode-orchestrator/package.json` | Extension + Marketplace train (**same** as CLI / VERSION) |
| `orchestrator.publishedCliVersion` default | One-click host install pin (**same** as VERSION) |
| hatch wheel metadata | Often **core only** `X.Y.Z` (see `pyproject.toml` pattern) — intentional for pre-releases |

**Product rule:** host CLI, template stamp, and VS Code extension share one semver. Marketplace
must publish **higher** than the live marketplace listing (never re-ship an already-live version
as “next”). After bump: `node scripts/npm/sync-version.js` then `python3 scripts/check-version-alignment.py`.

Check alignment on the template repo:

```bash
python3 scripts/check-version-alignment.py
python3 scripts/check-version-alignment.py --remote
```

## Three clocks (never conflate)

| Clock | Question | Command / file |
|-------|----------|----------------|
| **Host CLI** | What `orchestrator` binary is on PATH? | `orchestrator version` → `host` / package |
| **Template** | What would this CLI *deploy* into an app? | `VERSION` via template root (bundled or checkout) |
| **App lock** | What did this *app repo* last install? | `.orchestrator-version` → `version` |

```bash
orchestrator version                 # matrix for cwd
orchestrator version /path/to/app
orchestrator version --json
orchestrator status /path/to/app
```

## What to run when something is behind

| Situation | Action |
|-----------|--------|
| Host CLI behind template / release | `orchestrator self-upgrade --to 1.9.5 --yes` or `bash scripts/install.sh --uv-tool` |
| App lock behind template | `orchestrator upgrade /path/to/app --from-github v1.9.5 --yes --no-pr` |
| App install missing on other branches | `orchestrator install-persist .` (on a branch that has the lock) |
| Template source repo | **Do not** `init` yourself — not a consumer app |

## Lock file shape

```json
{
  "version": "1.9.5",
  "release_tag": "v1.9.5",
  "profile": "laravel",
  "cli_version": "1.9.5",
  "installed_at": "…",
  "ssot": "VERSION"
}
```

- `version` / `cli_version`: **no** leading `v`
- `release_tag`: **with** `v`
- `cli_version`: host CLI at install time (may later lag after `self-upgrade`)

## Project-global install vs version

`install-persist` does **not** change the version number; it makes the **current** lock + surfaces survive branch switches via `orchestrator/installed` + post-checkout.

## Bumping a release (template maintainers)

1. Set `VERSION` to **next** semver (**must be > marketplace-live**, e.g. live 2.2.1 → ship 2.2.2)
2. Sync mirrors: `node scripts/npm/sync-version.js` (root pkg + stamp + **extension** + CLI pin)
3. Verify: `python3 scripts/check-version-alignment.py` (CLI pin + extension must match)
4. Regenerate bundle hashes: `python3 scripts/orchestrator-bundle-hash.py generate`
5. Tag `vX.Y.Z`, publish GitHub release (wheel **and** VSIX both `X.Y.Z`)
6. Refresh host package: `bash scripts/install.sh --uv-tool` or pip/uv wheel for **same** `X.Y.Z`
7. Marketplace: upload **same** `orchestrator-memory-X.Y.Z.vsix` (not an older patch)
8. Apps: per-app `upgrade --from-github vX.Y.Z` then `install-persist` if needed
