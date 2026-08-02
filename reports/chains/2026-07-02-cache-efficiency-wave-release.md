# Cache-efficiency wave release — 2026-07-02

## Package (items 1–11)

| # | Deliverable | Path / command |
|---|-------------|----------------|
| 1 | MCP-first default | `.grok/config.toml` (`orchestrator-host`), `scripts/mcp-host-stdio.sh` |
| 2 | Registry cap alignment | `scripts/reconcile-cache-caps.py` (31 chains, 7 loops) |
| 3 | Section index | `docs/codebase/SECTIONS.md`, `scripts/generate-cache-sections.py` |
| 4 | Token auto-lean | `cache-efficient` + `token-usage-meter` skills |
| 5 | Slim chain skill | `.grok/skills/chain/SKILL.md` + `references/workflow.md` |
| 6 | Registry discipline | `github-expert`, `loop-engineering` |
| 7 | INDEX refresh | `.grok/memories/INDEX.md` |
| 8 | session-start skips | `chains/registry.yaml` session-start steps |
| 9 | Cache lint | `scripts/cache_efficiency_lint.py` |
| 10 | Lean deploy bundle | `deploy-bundle.yaml` → `cache-spine` selection |
| 11 | CLI wave | `orchestrator wave [--apply|--commit]` |

## Wave deploy — REVERTED 2026-07-02

**Fleet revert:** Unauthorized full copy of `chains/registry.yaml`, `docs/codebase/*`, manifests
was reverted on all wave apps (`git revert` of cache wave commit). google-stats app wiring
(`google-stats-ops`, `google-stats-script-expert`) restored.

**Correct policy (skills-only):**

```bash
bash scripts/deploy-cache-efficiency-wave.sh   # skills only — never registry/docs
```

**Forbidden on selective wave:** `chains/registry.yaml`, `CHAIN.md`, `patterns/`, `docs/codebase/`,
manifests, `sync_grok_to_github_claude.py` auto-run.

**Wave deploy source branches:** `master` or `develop` only (`scripts/wave-deploy-guard.sh`).

**Fleet repair (2026-07-02):** Revert commits pushed on all wave apps; google-stats registry wiring restored.

**Orchestrator merge:** PR #79 → develop; PR #81 → master.

## Verification

```bash
bash scripts/chain-audit.sh
python3 scripts/cache_efficiency_lint.py
python3 scripts/sync_grok_to_github_claude.py
```

## Fleet maintenance (deferred)

e-ndsign / ndestates-io cache-freshness-watch — run after wave lands.