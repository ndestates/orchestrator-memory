# Versioning (host · template · app)

[UPDATED 2026-07-31]

## Single source of truth

| Artifact | Role |
|----------|------|
| **`VERSION`** | **SSOT** — full product identity (`1.9.5` or `1.9.0-pre.5`) |
| `scripts/orchestrator-template-version` | Deployed stamp apps/session-check read |
| `package.json` `version` | npm wrapper (must match `VERSION`) |
| hatch wheel metadata | Often **core only** `X.Y.Z` (see `pyproject.toml` pattern) — intentional for pre-releases |

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

1. Set `VERSION` (and keep stamp/`package.json` in sync — `node scripts/npm/sync-version.js`)
2. Regenerate bundle hashes if required
3. Tag `vX.Y.Z`, publish GitHub release
4. Refresh host package: `bash scripts/install.sh --uv-tool`
5. Apps: per-app `upgrade --from-github vX.Y.Z` then `install-persist` if needed
