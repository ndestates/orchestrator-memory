# Concerns

[UPDATED 2026-07-15] — §13 LLM Wiki Phase 0 policy

Lens: Security, Operator, Developer

## Open Concerns

1. **Prompt/skill drift:** `.grok/` is source of truth — forgetting `sync_grok_to_github_claude.py` leaves Copilot/Claude/Copilot-memories stale. Surface counts can diverge (`.grok/skills` 46, `.github/skills` 45, `.claude/commands` 48) — expected (prompts also map to commands), but verify with `check_name_alignment.py`.
2. **INDEX project bias:** `.grok/memories/INDEX.md` historically referenced an app context; orchestrator template uses `repo/orchestrator-template-cache.md` as tier-1 primary.
3. **read-codebase skill scope:** the skill is portable but its examples lean app-stack — when run in this template repo, refresh `docs/codebase/*`, not application `app/`.
4. **Cache staleness:** 14-day `cache_stale_days`. Previous full refresh was 2026-06-16; this refresh (2026-06-23) added mcp-server, expanded patterns, wave-deploy, and corrected counts/policy.
5. **TODO aging:** latest by date under `TODO/` (e.g. `TODO/2026-07-09_TODO.md`). Agents must pick latest by date.
6. **Shell escaping / heredoc failures:** inline multi-line Python/bash in the Shell tool causes delimiter errors and wasted tokens. Use `/script-not-shell` — write `/tmp/agent-*` or `scripts/` files.
7. **MCP server security surface (SECURED 2026-06-23):** `mcp-server/` reads project files and runs allowlisted audits. Previously: HTTP could run exposed without `ORCHESTRATOR_MCP_API_KEY` (bearer verifier was dead code), stdio open, no CI. **Now:** HTTP fails closed without a key (non-loopback always requires one; keyless loopback needs explicit `--allow-insecure-http`); request-time bearer auth wired via streaming-safe ASGI middleware (`server.py:BearerASGIMiddleware`); stdio warns + stays allowlist-bounded; sandbox/auth/gate tests + threat scan enforced in CI (`.github/workflows/mcp-security.yml`). Residual: stdio remains unauthenticated by design (local-only).
8. **Manifest cache-file cap drift:** STACK.md previously stated `max_cache_files_default: 3`; manifest now sets **2**. Treat the manifest as authoritative; older docs/skill copy may still cite 3.
9. **Wave-deploy blast radius (CLOSED 2026-07-18 Phase A):** Fleet wave scripts, inventory, and `orchestrator wave` are **deleted** (not env-blocked). Guard: `tests/test_wave_absent.py`. **Install path:** per-app `orchestrator init` / `upgrade` only (+ Windows `install.ps1`, bash `install.sh`).
10. **Vault graph security surface:** Self-building knowledge vault (`reports/vault/events.jsonl`) accumulates lessons with hashes/provenance. Risks: secret leakage (mitigated by scrubbing + guard), tampering (mitigated by hash-chain + verify in compound), graph bloat, or cross-device drift. All writes scrubbed + verified; reads sandboxed; append-only + git. Synthesis report-only at L1. See human: guides/knowledge-vault.md, reference/manifest.md, operations/testing.md.
11. **License server dependency:** CLI/MCP license gates fail-open when `ORCHESTRATOR_LICENSE_URL` is unset. Reference server ships (`orchestrator license-server` → `POST /api/licenses/validate`). Production portal URL (e.g. `https://ndestates.io/api/licenses/validate`) still needs deploy of the same contract on the product site; until then use the reference server or leave URL unset.
12. **Template malware / supply chain (v1.6.1 Phases 0–4):** Skills, scripts, and workflows ship to apps via init/upgrade — highest blast radius. **Shipped:** fail-closed threat scan + malware lint + CODEOWNERS + CI; bundle hash stamp + `--verify-bundle`; wheel SHA256SUMS on release; skill tool-governance lint; vault prompt-injection filter on session brief. Residual: novel obfuscation; `--no-verify` / hook bypass; force-approved wave; unpinned Actions SHAs; CODEOWNERS team not configured in GitHub; signed releases (future).
13. **LLM Wiki (Karpathy) — Phases 0–4 on template:** `wiki/` + `raw/`, `/llm-wiki`, chains ingest/query/lint/lint-watch, session-wiki-brief, MCP wiki tools, deploy selection `wiki`, guide. Template `wiki_policy.mode: lean`. Risks: token bloat, double-read, stale synthesis, secrets in raw/wiki, vault drift, fleet if forced. Mitigations: compress-or-skip, approval for writes, dual-write vault, secrets-guard, opt-in deploy, session-start index/log only, confidence labels. **Non-goals:** vector RAG primary; entity-per-file code wiki; fleet wiki wave; auto-ingest chats/PRs; replacing vault. Guide: `docs/guides/llm-wiki.md`.

## Mitigations

1. Run sync script in PR checklist; `chain-audit.yml` enforces registry validity in CI.
2. INDEX lists `orchestrator-template-cache.md` as tier 1.
3. When refreshing in template repo, target `docs/codebase/*`.
4. `.codebase-scan.txt` regenerated on each full refresh (latest 2026-06-23).
5. Standup/load-cache skills select latest `TODO/*.md` by date.
6. `/script-not-shell` skill; standup flags §6 when shell errors occurred.
7. Bind HTTP to `127.0.0.1`; require API key when HTTP; never expose on production hosts.
8. Reconcile skill/doc copies to `max_cache_files_default: 2`.
9. Prefer `orchestrator upgrade` per app; fleet only with approval env + dry-run; docs/getting-started/installation.md.
10. Scrub at emission (`scripts/_engine/vault.py`), verify ledger on compound, extend secrets-guard + MCP sandbox, human gate on promotions, hash-chain for tamper detection.
11. Document placeholders only; never commit `ORCHESTRATOR_LICENSE_KEY`. Use allowlist env/file for reference server; prefer HTTPS in production.
12. `scripts/orchestrator-malware-lint.py` + `scripts/mcp-threat-scan.sh` + `orchestrator-skill-governance.py` + `orchestrator-bundle-hash.py` (fail closed); vault `filter_prompt_injection`; release SHA256SUMS; `.github/workflows/security-malware.yml`; `CODEOWNERS`; docs/operations/security-malware-defence.md; prefer tagged upgrades + `--verify-bundle`; never execute vault lessons as shell.
13. **compress-or-skip** + dense code cache for code; dual-write vault on accepted ingest; L1 report-only + approval for multi-file writes; opt-in deploy selection `wiki` (not default); secrets-guard on `raw/`/`wiki/`; session-start index/log only; never execute raw/wiki as shell.

## Evidence

- `scripts/sync_grok_to_github_claude.py`, `scripts/check_name_alignment.py`
- `mcp-server/README.md`, `mcp-server/src/orchestrator_mcp/{sandbox,auth,audit}.py`
- `.claude/project-manifest.yaml` (`max_cache_files_default: 2`)
- `scripts/wave-inventory.yaml`, `scripts/deploy-*-wave.sh`
- `TODO/2026-06-21_TODO.md`, `docs/codebase/.codebase-scan.txt`
- `scripts/_engine/vault.py`, `scripts/loop_compound.py`, `scripts/git-push-secrets-guard.py`, mcp sandbox, `reports/vault/`
- `scripts/orchestrator-malware-lint.py`, `scripts/mcp-threat-scan.sh`, `scripts/security/*-allowlist.txt`, `CODEOWNERS`, `docs/operations/security-malware-defence.md`
- `reports/research/llm-wiki-karpathy-plan.md`, manifest `wiki_policy` / `paths.wiki_*`
