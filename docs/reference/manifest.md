# Manifest reference

[UPDATED 2026-07-15] — wiki_policy + wiki paths (Phase 1, mode lean on template)

## Overview

`.github/project-manifest.yaml` is the **canonical** source of truth for paths and policies. Identical content is synced to each AI platform directory so users are not blocked when they only have one tool installed.

| Platform | Manifest path |
|----------|----------------|
| GitHub Copilot (canonical) | `.github/project-manifest.yaml` |
| Claude Code | `.claude/project-manifest.yaml` |
| Grok Build | `.grok/project-manifest.yaml` |
| Google Gemini | `.gemini/project-manifest.yaml` |
| Copilot workspace | `.copilot/project-manifest.yaml` |
| Cursor IDE | `.cursor/project-manifest.yaml` |

**Sync:** after editing the canonical file, run `python3 scripts/sync_manifests.py` (also runs at the end of `scripts/sync_grok_to_github_claude.py`).

## Vault paths (for self-building knowledge graph)

From manifest `paths`:
- `vault_events_dir: "reports/vault"`
- `vault_ledger: "reports/vault/events.jsonl"`

The ledger is a content-hashed, append-only graph of lessons/events (see `scripts/_engine/vault.py`, loop-compound integration, secure scrubbing + verification). Used for provenance in compound learning and self-synthesis.

## Wiki paths (LLM Wiki / Karpathy pattern — Phase 1)

From manifest `paths` (template ships `wiki/` + `raw/` scaffold):

| Key | Default | Purpose |
|-----|---------|---------|
| `wiki_dir` | `wiki` | LLM-maintained wiki root |
| `wiki_raw_dir` | `raw` | Immutable source drop zone |
| `wiki_index` | `wiki/index.md` | Content catalog |
| `wiki_log` | `wiki/log.md` | Append-only ops log |

Policy block: **`wiki_policy`** (default `mode: off`). Full decisions: [LLM Wiki plan](../../reports/research/llm-wiki-karpathy-plan.md).

| Key | Default | Purpose |
|-----|---------|---------|
| `mode` | `lean` (template) | `off` \| `lean` \| `full` — agents must not run wiki ops when `off` |
| `l1_report_only` | `true` | Lint/ingest propose only at L1 |
| `require_approval_for_writes` | `true` | Human gate for multi-file apply |
| `compress_or_skip` | `true` | Page only if ≥2 sources or non-greppable narrative |
| `max_wiki_pages_per_session` | `2` | Cap after index/log (separate from code cache cap) |
| `session_start_load` | `index_log_only` | No full-wiki load at session-start |
| `dual_write_vault` | `true` | Vault event on accepted ingest |
| `deploy_selection` | `wiki` | Future opt-in deploy bundle name |
| `auto_ingest` | `false` | No silent batch ingest |

**Do not confuse** wiki with `docs/codebase/` (code cache) or vault ledger (integrity graph).

## Before you begin

Open the manifest for **your** platform (table above) — **not** another host’s copy as primary.
See [platform-surfaces.md](platform-surfaces.md): Grok→`.grok/`, Claude→`.claude/`, Copilot→`.github/`, etc.
If the host is unknown, `.github/project-manifest.yaml` is the canonical fallback.

### Identity gate (required — any model)

After reading the manifest (file or MCP `get_project_manifest`), agents must confirm it describes **this** repository and is not leftover orchestrator **Project Template** defaults:

```bash
python3 scripts/check-project-manifest.py --json
```

| `status` | Meaning |
|----------|---------|
| `ok` | Customized for this app, or legitimate orchestrator source repo |
| `warn` | Partial mismatch with repo signals |
| `template_residue` | Still stock template name/description/generic stack on an app |
| `missing` | No platform manifest found |

MCP returns the same under `identity` / `identity_briefing`. Customize `project.name`, `stack.*`, and `runtime.environment_manager` after deploy — see template-decontaminate / per-app upgrade guides.

**MCP is develop-only:** session-start uses `bash scripts/detect-project-runtime.sh --with-manifest-identity`. When MCP is not ready, offer DDEV / Docker Compose / host stdio start options. Never run MCP on publicly hosted environments (DigitalOcean App Platform, public K8s, etc.).

## Key sections

### `project`

| Field | Purpose |
|-------|---------|
| `name` | Display name (**must not** remain `"Project Template"` on app repos) |
| `description` | App summary (not the stock orchestrator template blurb) |
| `default_branch` | Production branch (`master`) |

### `stack`

| Field | Values | Purpose |
|-------|--------|---------|
| `framework` | generic, laravel, … | Drives doc and skill selection |
| `language` | generic, php, … | Runtime assumptions |
| `uses_database` | true/false | Test safety context |

### `paths`

| Field | Default | Purpose |
|-------|---------|---------|
| `todo_dir` | `TODO` | Daily TODO files |
| `docs_index` | `docs/codebase/README.md` | Cache entry |
| `chain_registry` | `CHAIN.md` | Human chain index |
| `chains_dir` | `chains` | Machine chain catalog |
| `wiki_dir` | `wiki` | LLM wiki root (Phase 0 reserved) |
| `wiki_raw_dir` | `raw` | Immutable wiki sources |
| `wiki_index` | `wiki/index.md` | Wiki catalog |
| `wiki_log` | `wiki/log.md` | Wiki ops log |

### `wiki_policy`

See [Wiki paths](#wiki-paths-llm-wiki--karpathy-pattern--phase-1) above. Template default **`mode: lean`** after Phase 1; apps may stay `off` until they deploy selection `wiki`.

### `token_policy`

| Field | Purpose |
|-------|---------|
| `mode` | `lean` (default), `standard`, `deep` |
| `max_cache_files_default` | Max **extra** `docs/codebase/*` files after the spine (see below) |
| `grep_before_read` | Grep headings/patterns before full-file reads |
| `no_source_until_confirmed` | No app source reads until user confirms direction |
| `session_refresh_context_tokens` | Suggest new session when Grok context exceeds this |
| `cache_stale_days` | When to run `/read-codebase` |

#### `max_cache_files_default` explained

This is the **hard cap on additional cache documents** agents may load from `paths.docs_dir` (`docs/codebase/`) in **lean** mode after the always-on spine:

| Always loaded (does **not** count) | Counts toward cap |
|-----------------------------------|-------------------|
| `.claude/project-manifest.yaml` | Each extra `docs/codebase/*.md` beyond the index |
| `paths.docs_index` (`README.md`) | Each memory file picked from `.grok/memories/INDEX.md` |
| Latest `TODO/*.md` | |
| `.grok/memories/INDEX.md` | |
| `docs/codebase/.codebase-scan.txt` (freshness) | |

**Default `2`** means: read the index, then pick **at most two** topic files (e.g. `CONCERNS.md` + `ARCHITECTURE.md`, or `CONCERNS.md` + one task-specific doc). Use **section reads** (`offset`/`limit`) or **grep** — not full files when possible.

`standard` / `deep` modes may raise this in prompts; `lean` is the template default.

### `chain_policy`

| Field | Purpose |
|-------|---------|
| `shared_cache_across_steps` | One cache load per chain |
| `max_handoff_tokens` | 80 — between chain steps |
| `allow_opt_out` | User can say `no chain` |
| `require_confirm_before_run` | Confirm inferred chains |
| `scheduled_allowlist` | Chain ids that skip confirm when invoked with explicit id + `scheduled` (or `CHAIN_SCHEDULED=1`) |

### `loop_policy`

| Field | Purpose |
|-------|---------|
| `default_level` | L1 report-only |
| `cache_first_mandatory` | Loops must load cache first |

## Verify

Manifest YAML parses and paths referenced exist.

## Next steps

- [Cache and token savings](../guides/cache-and-token-savings.md) — lean vs deep, worked size comparison, how to measure
- [Chains](chains.md) — chain catalog
- [Skills](skills.md) — skill catalog
- [Architecture cache](../codebase/ARCHITECTURE.md)

## Related

- [Reference index](index.md)