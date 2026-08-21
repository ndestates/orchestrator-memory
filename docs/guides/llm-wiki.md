# LLM Wiki (Karpathy pattern)

[UPDATED 2026-07-15] — Phases 0–4 on template

## Overview

The orchestrator ships a **persistent, LLM-maintained markdown wiki** (inspired by [Karpathy’s llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Knowledge is **compiled** into `wiki/` and updated on ingest—not re-derived from raw files on every question.

| Layer | Path | Role |
|-------|------|------|
| Raw (immutable) | `raw/` | Sources agents never edit after commit |
| Wiki (LLM-owned) | `wiki/` | Summaries, concepts, decisions, index, log |
| Schema | `/llm-wiki` + `wiki_policy` | Ingest / query / lint discipline |
| Code cache | `docs/codebase/` | Dense maps for greppable **code** (not entity sprawl) |
| Vault | `reports/vault/events.jsonl` | Integrity + compound graph (not a browsable wiki) |

Full product plan: [llm-wiki-karpathy-plan.md](../../reports/research/llm-wiki-karpathy-plan.md).

## Before you begin

- Manifest: `wiki_policy.mode` is `lean` on this template; use `off` on apps until ready.
- Session: `/chain session-start` runs a **lean** wiki brief (log + open questions only).
- Secrets: never put keys, tokens, or PII in `raw/` or `wiki/`.

## Daily ops

| Goal | Command |
|------|---------|
| Session brief | `python3 scripts/session-wiki-brief.py` (also MCP `wiki_status`) |
| Ask the wiki | `/chain wiki-query` or `/llm-wiki query …` |
| Ingest one source | Drop under `raw/…` → `/chain wiki-ingest` |
| Health check | `/chain wiki-lint` or `python3 scripts/wiki_lint_check.py` |
| L1 watch | `/chain wiki-lint-watch` (manual; host: `bash scripts/loop-wiki-lint-host.sh`) |

### Confidence labels

Query answers must end with `confidence: strong | moderate | weak` and cited wiki paths.

### Compress-or-skip

Create a page only if it **compresses ≥2 sources** or non-greppable narrative. Code facts stay in `docs/codebase/`.

## Session-start (Phase 2)

After vault brief:

```bash
python3 scripts/session-wiki-brief.py
```

Agents must not load the full wiki. Cap content pages with `max_wiki_pages_per_session`.

## EOD (Phase 2)

`/chain eod-shutdown` **offers** 0–2 file-back insights into `wiki/queries/` — never auto-writes.

## Research (Phase 2)

After research memo: snapshot to `raw/research/`, then optional `/chain wiki-ingest`.

## MCP (Phase 2)

| Tool | Purpose |
|------|---------|
| `wiki_status` | Lean brief JSON |
| `wiki_search_index` | Search index / paths |
| `wiki_read_page` | Bounded read under `wiki/` or `raw/` |
| `run_readonly_audit` audit=`wiki` | `wiki_lint_check.py` |

Sandbox allows `wiki/` and `raw/` reads only (no writes via MCP).

## Deploy to an app (Phase 4)

```bash
# From orchestrator template:
python3 scripts/deploy_grok_to_project.py /path/to/app --selections wiki --dry-run
# Then set wiki_policy.mode: lean in the app manifest (if still off).
```

Not in `default_selections`. Never fleet-default.

## CI / lint (Phase 3)

```bash
python3 scripts/wiki_lint_check.py          # exit 1 on fail
python3 scripts/wiki_lint_check.py --strict # fail on warn too
```

## Related

- Skill: `.grok/skills/llm-wiki/SKILL.md`
- Schema: `.grok/skills/llm-wiki/references/wiki-schema.md`
- Chains: `wiki-ingest`, `wiki-query`, `wiki-lint`, `wiki-lint-watch`
- Vault: [knowledge-vault.md](knowledge-vault.md)
