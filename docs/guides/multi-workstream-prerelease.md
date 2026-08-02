# Multi-workstream → stable **v1.9.0**

[UPDATED 2026-07-23]

## Stable vs pre-release

| Channel | Tag | Use |
|---------|-----|-----|
| **Stable (current)** | **`v1.9.1`** (Latest) | Production apps, default upgrade target |
| Previous stable | `v1.9.0` | Rollback / prior multi-workstream ship |
| Older stable | `v1.8.9` | Rollback only |
| Pre-releases (superseded) | `v1.9.0-pre.1` … `v1.9.0-pre.5` | Historical only — **do not ship new pre labels for this line** |

**App `project-manifest.yaml` does not need a version field change.**  
Upgrade copies skills, chains, scripts, and platform surfaces. Stack/token_policy stay as today.

## Upgrade (stable)

```bash
# Dry-run first (no --yes)
orchestrator upgrade /path/to/app --from-github v1.9.1

# Apply
orchestrator upgrade /path/to/app --from-github v1.9.1 --yes --no-pr
```

After upgrade, confirm runtime scripts exist:

```bash
ls scripts/workstream.py scripts/workstream_worktree.py scripts/workstream_guard.py \
   scripts/workstream_prompts.py scripts/workstream_recommend.py \
   scripts/resume-branch.sh scripts/session-context-envelope.py scripts/mcp-smoke.sh
```

Multi-LLM surfaces:

```bash
orchestrator upgrade /path/to/app \
  --from-github v1.9.1 \
  --selections grok,claude,copilot,chatgpt,gemini,cursor,chains,scripts,cache-spine \
  --yes --no-pr
```

Private repo: `export GITHUB_TOKEN=…` (or `GH_TOKEN`).

## Session-start branch policy (1.9.0)

| Rule | Behaviour |
|------|-----------|
| **Fetch** | `git fetch origin --prune` at session-start |
| **Target** | `remote_last` = newest `origin/*` feature tip (excludes master/develop) |
| **Vault** | Secondary only; never blocks remote_last when clean |
| **Switch** | Auto when tree clean (`resume-branch.sh --apply`); **block** if dirty |
| **After switch** | Refresh vault workspace pointer to the new branch |

Do **not** release further `1.9.0-pre.*` tags for this fix — ship **`v1.9.0`**.

## After upgrade — operator commands

```text
/chain session-start
/multi-workstream list
/multi-workstream diamond
/multi-workstream serial
/multi-workstream guard
/multi-workstream prompts
/multi-workstream worktree list
/web-cache-expert
/chain web-cache-review
```

- **`diamond`**: Shape B **recommendation** only (safe parallel + blocked held). No auto-run.
- **`serial`**: primary-only plan (alternative to diamond).
- **`worktree`**: isolate a feature branch under parent of main repo (never merges for you).
- **`prompts` / `ready`**: merge-ready / open-PR / WIP / frozen guidance — still no auto-merge.
- **`guard`**: integrity check (primary active, no protected branches on tracks).
- Workstream **`id`**: name in `reports/sessions/workstreams.yaml`, not TODO line numbers.
- **`/web-cache-expert`**: site HTTP/CDN/image/document caching (not AI `/cache-efficient`).

## Roll back

```bash
orchestrator upgrade /path/to/app --from-github v1.8.9 --yes --no-pr
```

## Project manifest notes

| Question | Answer |
|----------|--------|
| Must app bump stamp? | Stamp is **`1.9.1`** (full stable, not pre) |
| New required manifest keys? | **None** |
