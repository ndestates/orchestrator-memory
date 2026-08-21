# Memory index (read this first — do not load all memories)

**Orchestrator template** (`ndestates/orchestrator`): manifest-first, cache-first prompt/agent system. Grok source in `.grok/`; synced to `.github/` (Copilot) and `.claude/` (Claude Code). Loops + chains for token-efficient composition.

**Goal:** Pick ≤2 tier-2 files below. Pair with `docs/codebase/README.md` + `docs/codebase/SECTIONS.md` + latest `TODO/*.md`.

## Always (tier 1)

| File | When |
|------|------|
| `docs/codebase/README.md` | Every session (refreshed 2026-06-30) |
| `docs/codebase/SECTIONS.md` | Section grep-before-read index (generated) |
| `docs/codebase/.codebase-freshness.txt` | Lean freshness + stack (cache-efficient spine) |
| `docs/codebase/.codebase-scan.txt` | Full scan artifact — **never** Read in lean mode |
| `docs/codebase/CONCERNS.md` | Open risks (numbered) |
| Latest `TODO/*_TODO.md` | Current scope (`TODO/2026-07-02_TODO.md`) |
| `.grok/memories/who-i-am.md` | Operator profile (after `bash scripts/setup-who-i-am.sh`) — persistent "who I am" |
| `repo/orchestrator-template-cache.md` | Template architecture, commands, branch flow |
| `repo/installer-distribution.md` | Installer truth: #116 + npm port 2026-07-11; no fleet auto-deploy |

## Grok topic files (tier 2)

| File | Load if task involves… |
|------|------------------------|
| `2026-06-05-grok-caching-setup.md` | Initial .grok setup history |
| `CHAIN.md` / `chains/registry.yaml` | Skill chaining — **grep id only** or MCP `get_chain_detail` |
| `LOOP.md` / `STATE.md` | Loop triage, L1 reports |
| Skills: `chain`, `loop-triage`, `cache-efficient`, `cache-freshness-check`, `script-not-shell` | Composition, lean mode, cache staleness, shell discipline |
| `reports/research/prompt-patterns.md` | Authoring skills, prompts, agents |
| `reports/research/grok_usage_guide.md` + `who-i-am-profile-template.md` | Multi-AI adoption, techniques, profile reference |
| `.grok/prompts/multi-ai-best-practices-setup.md` | One-shot multi-AI behavior setup |

## Repo memories (`repo/`)

| File | Load if task involves… |
|------|------------------------|
| `orchestrator-template-cache.md` | General template work, standup, sync, workflows |

## Rules

- Cite exact cache/memory path + section.
- ≤2 tier-2 files per turn (`max_cache_files_default: 2`).
- MCP-first reads when `.grok/config.toml` has `orchestrator-host` or `orchestrator-ddev` enabled.
- Refresh when `.codebase-freshness.txt` exceeds `cache_stale_days` (14).