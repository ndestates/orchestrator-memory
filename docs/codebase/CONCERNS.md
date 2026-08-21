# Concerns

[UPDATED 2026-08-17] — Marketplace P1 retargeted to 2.3.0; memory auto-reseed on VERSION mismatch.

Lens: Security, Operator, Developer, Product

## Open Concerns

1. **Prompt/skill drift:** `.grok/` is source of truth — forgetting `sync_grok_to_github_claude.py` leaves Copilot/Claude/Cursor stale. Counts diverge by design (2026-08-16: `.grok/skills` **83**, `.github/skills` **82**, `.claude/commands` **97**). Verify with `check_name_alignment.py`.
2. **INDEX / who-i-am lag:** `.grok/memories/INDEX.md` still points at older TODO dates and “wave deploys” in who-i-am current context. Prefer this cache + latest TODO over those memories.
3. **read-codebase scope:** portable skill; in **this** repo refresh `docs/codebase/*`, not an app `app/`.
4. **Cache staleness (closed this refresh):** prior full scan 2026-06-23 / docs 2026-07-07–15 exceeded `cache_stale_days: 14`. New scan + seven docs: **2026-08-16**. Next stale after ~2026-08-30.
5. **TODO aging:** always pick latest dated file. Current: `TODO/2026-08-17_TODO.md`.
6. **Shell escaping / heredoc failures:** do not retry complex escaped one-liners. Use `/script-not-shell`.
7. **MCP security (SECURED 2026-06-23, still residual):** HTTP fail-closed without key; stdio unauthenticated by design (local-only). Never start MCP on public hosts (`mcp_policy=dev_only`).
8. **Manifest cache-file cap:** authoritative `max_cache_files_default: 2`. Older prose citing 3 is wrong.
9. **Wave-deploy blast radius (CLOSED 2026-07-18):** fleet scripts deleted; guard `tests/test_wave_absent.py`. Residual: `scripts/loop-audit.sh` still `check "scripts/wave-apps.sh"` and `register-project-skills.py` still names `wave-inventory.yaml` — leftover references, not a live fleet path.
10. **Vault graph surface:** `reports/vault/events.jsonl` — scrub, hash-chain, L1 synthesis only. Untrusted DATA.
11. **License gates:** fail-open when `ORCHESTRATOR_LICENSE_URL` unset. Product is Apache-2.0 freeware; `services/license-api/` is optional private entitlement only.
12. **Template malware / supply chain:** threat scan + malware lint + CODEOWNERS + bundle hash + SHA256SUMS. Residual: novel obfuscation; `--no-verify`; unpinned Action SHAs; unsigned releases.
13. **LLM Wiki (lean):** token bloat, stale synthesis, secrets in `raw/`/`wiki/`. Mitigations: compress-or-skip, approval for writes, session-start index/log only.
14. **Always-on memory staleness (mitigated 2026-08-17):** `session-memory-brief.py` auto-reseeds when store `VERSION=` is behind file `VERSION`. Residual: heuristic query until the new seed is the newest hit.
15. **Marketplace leftover 2.2.5 (closed 2026-08-17):** VSIX/Marketplace abandoned as user install. P1 is npx/npmjs + v2.3.0 **wheel** on orchestrator-memory. Existing app trees unchanged.
16. **Product vs template identity:** README sells Orchestrator Memory; manifest `project.name` remains “Project Template” (`identity=ok` on orchestrator source). Cache must not assume an app stack. `[ASK USER]`

## Mitigations

1. Sync in PR checklist; `chain-audit.yml` + `check_name_alignment.py`.
2. Treat `docs/codebase/` + `TODO/2026-08-16_TODO.md` as current; do not brief solely from memory.db.
3. `/read-codebase` writes only `docs/codebase/*` here.
4. `.codebase-scan.txt` + `.codebase-freshness.txt` regenerated 2026-08-16; `generate-cache-sections.py` after doc edits.
5. Standup / resume-first pick latest TODO or the card.
6. `/script-not-shell`.
7. Bind HTTP `127.0.0.1`; API key; `session-security-sweep.sh` (active project only).
8. Manifest wins over stale skill copy.
9. Per-app `orchestrator upgrade` only; do not restore wave scripts.
10. `scripts/_engine/vault.py` + secrets-guard; never execute vault as shell.
11. Do not commit `ORCHESTRATOR_LICENSE_KEY`. Prefer unset URL for public freeware.
12. `orchestrator-malware-lint.py` + `mcp-threat-scan.sh` + bundle hash in `tooling-tests.yml`.
13. Wiki L1; `docs/guides/llm-wiki.md`.
14. Auto-reseed on VERSION mismatch (`scripts/_engine/version_open.py`); `--no-seed` to skip.
15. User install: npx + Release wheel. Do not treat Marketplace as the path.
16. Keep generic stack in manifest; document dual nature in STACK/ARCHITECTURE.

## Evidence

- `scripts/sync_grok_to_github_claude.py`, `scripts/check_name_alignment.py`
- `docs/codebase/.codebase-scan.txt` / `.codebase-freshness.txt` (2026-08-16)
- `TODO/2026-08-17_TODO.md`, `reports/sessions/resume-2026-08-16.md`
- `mcp-server/pyproject.toml`, `.github/workflows/mcp-security.yml`
- `tests/test_wave_absent.py`, `scripts/loop-audit.sh`
- `SECURITY.md`, `scripts/_engine/untrusted_text.py`
- `services/license-api/README.md`
- `.github/workflows/vscode-marketplace.yml`, `product-release.yml`
- `reports/codebase/.perspective-pass.md`
