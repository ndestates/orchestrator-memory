# Bug Hunt Report — efficiency (orchestrator template)

**Date:** 2026-07-11  
**Mode:** scan → **Phase A fix applied**  
**Branch:** `feature/mcp-host-compound-vault-security-2026-07-11`  
**Backup ID:** `2026-07-11T122301Z`  
**Rollback:** `python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id 2026-07-11T122301Z`  
**Cache cited:** manifest, `docs/codebase/CONCERNS.md`, `docs/codebase/TESTING.md`, efficiency grep artifact  

## Executive summary

- Focused on **performance & resource** inefficiencies in Python hot paths (`scripts/`, `src/`, MCP), not app N+1 (no app DB).
- **10 findings:** 0 critical, 0 high, **4 medium**, **4 low**, **2 info**.
- **Phase A fixed (2026-07-11):** BH-001, BH-004, BH-005, BH-007. Phase B/C still open.
- Microbench after BH-001: 50 appends after 500 events ≈ **0.075s** (was ~0.15s).
- Tests: vault pointer + skill governance + token_monitor parse — **pass**.

## Findings

| ID | Sev | Cat | Location | Summary | Status |
|----|-----|-----|----------|---------|--------|
| BH-001 | medium | perf | `scripts/_engine/vault.py` `append_event` | Full-ledger `read_text` + parse every append for hash dedupe | **fixed** |
| BH-002 | medium | perf | `scripts/_engine/vault.py` `verify_ledger` | Parent existence via `any(... for e in events[:i])` → O(n²) | **fixed** |
| BH-003 | medium | perf | `mcp-server/.../helpers.py` `load_chains_registry` | Full `registry.yaml` (~2.8k lines) re-parsed every MCP chain call; no mtime cache | **fixed** |
| BH-004 | medium | perf | `token-usage-meter/.../token_monitor.py` | Same `updates.jsonl` fully read+parsed twice per sync | **fixed** |
| BH-005 | low | perf | `scripts/loop_compound.py` `append_state_lessons` | Double `STATE.md` read (existing lessons + rewrite) | **fixed** |
| BH-006 | low | ops/perf | `src/orchestrator_cli/gitops.py` `create_branch` | Always `checkout -b`; fails if branch exists (re-run upgrade friction) | **fixed** |
| BH-007 | low | token-waste | `scripts/orchestrator-skill-governance.py` | ~200 info findings for every shell-mention skill; noise for agents/CI logs | **fixed** |
| BH-008 | low | perf | `scripts/orchestrator-malware-lint.py` | Per-line allowlist is O(allow×lines); rules applied line-by-line | **fixed** |
| BH-009 | info | perf | `scripts/_engine/app_compound.py` `find_unclosed_report` | Reads **all** `reports/loops/*.md` until match (unbounded growth) | **fixed** |
| BH-010 | info | perf | `scripts/_engine/deploy.py` `collect_paths_from_spec` | `rglob("*")` over whole skill trees each upgrade (acceptable infrequent) | deferred |

### BH-001 — Vault append_event full-ledger scan (medium)

- **Category:** performance & resources  
- **Evidence:** `append_event` loads entire ledger into memory and parses every JSONL line on **each** append (comment claims “tail-scan” but implements full scan):

```210:234:scripts/_engine/vault.py
def append_event(ledger_path: Path, event: dict[str, Any]) -> None:
    ...
    if ch and ledger_path.is_file():
        try:
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                ...
                if existing.get("content_hash") == ch:
                    return
```

- **Impact:** Append cost grows O(n) per write → O(n²) for bulk emits (EOD, backfill, compound). Microbench: 50 appends after 500 events ≈ **0.15s** on this host; will worsen as vault grows across apps.  
- **Reproduction:** static + local microbench (see scan artifacts).  
- **Fix (suggested):**  
  1. Prefer **tail-only** check (last K lines) for double-emit races, **or**  
  2. Maintain in-memory/`seen_hashes` set for multi-append batch APIs, **or**  
  3. mmap/stream reverse read until parent line of same operator/type.  
- **Tests:** extend `tests/test_vault_workspace_pointer.py` with 2k-event append timing budget + correctness.

### BH-002 — verify_ledger parent scan O(n²) (medium)

- **Category:** performance  
- **Evidence:**

```274:278:scripts/_engine/vault.py
        for p in ev.get("parents", []):
            if not any(e.get("content_hash") == p for e in events[:i]):
                issues.append(...)
```

- **Impact:** Session-start + compound verify on large ledgers (thousands of events) becomes quadratic. At n=550 still ~4ms; at n=10k likely tens–hundreds of ms and growing. Relation check also scans full list per target.  
- **Fix (suggested):** Build `seen` set once while iterating (parents must already be in `seen_hashes`); for relations use full `seen` or hash index set.  
- **Tests:** `verify_ledger` on synthetic 5k-event ledger under budget (e.g. &lt;100ms).

### BH-003 — MCP registry YAML reloaded uncached (medium)

- **Category:** performance / token-adjacent latency  
- **Evidence:** `load_chains_registry` always `yaml.safe_load` of `chains/registry.yaml` (~2847 lines) with no process-level cache:

```37:61:mcp-server/src/orchestrator_mcp/helpers.py
def load_chains_registry(root: Path) -> dict[str, Any]:
    ...
    with composed.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
```

Used by `list_chains`, `get_chain_detail`, skill listing, etc.  
- **Impact:** Every MCP tool call that needs chains pays YAML parse cost; multi-step chains amplify.  
- **Fix (suggested):** Cache `(mtime, size) → parsed dict` in module globals; invalidate on mtime change. Optional: index chains by `id` for O(1) `get_chain_detail`.  
- **Tests:** unit test cache hit does not re-read file (mock open).

### BH-004 — token_monitor double full parse of updates.jsonl (medium)

- **Category:** performance  
- **Evidence:** `parse_session_model_id` and `parse_session_turns` each `read_text` + line-parse the same path:

```69:96:.grok/skills/token-usage-meter/scripts/token_monitor.py
def parse_session_model_id(updates_path: Path) -> str:
    for line in updates_path.read_text(...).splitlines():
        ...
def parse_session_turns(updates_path: Path) -> List[Dict[str, Any]]:
    for line in updates_path.read_text(...).splitlines():
```

- **Impact:** Session logs can be large; session-start sync pays **2×** I/O and JSON parse. Directly hits token/cost tooling path.  
- **Fix (suggested):** Single-pass parser returning `(model_id, turns)` or shared line iterator.  
- **Tests:** fixture updates.jsonl → one read (mock Path.read_text call count == 1).

### BH-005 — loop_compound double STATE.md read (low)

- **Category:** performance  
- **Evidence:** `append_state_lessons` calls `read_state_lessons` (read file) then `state_path.read_text` again for rewrite.  
- **Impact:** Minor (STATE.md small); pattern repeats in compound.  
- **Fix:** Single read; parse lessons + mutate text in memory.  

### BH-006 — create_branch never reuses existing branch (low)

- **Category:** ops / delivery efficiency  
- **Evidence:** `git checkout -b` only; re-running `orchestrator upgrade` after a failed mid-flight fails with exit 128. Seen during 1.6.1 app roll (mailchimp).  
- **Impact:** Wasted operator time and manual deploy workarounds.  
- **Fix:** If branch exists, `checkout` it (optionally require clean + same name); document behaviour.  

### BH-007 — skill-governance info flood (low)

- **Category:** token-waste / observability noise  
- **Evidence:** Default scan marks every shell-mention skill as `info` (~200). Critical path is tight (good).  
- **Impact:** CI log bloat; agents that dump findings waste context.  
- **Fix:** Default output **critical only**; `--info` for inventory. Optional write count-only summary.  

### BH-008 — malware-lint allowlist membership (low)

- **Category:** performance  
- **Evidence:** For each line: `any(a in blob or a in rel for a in allow)` then all RULES regex.  
- **Impact:** ~0.4s today on this repo — acceptable for CI; slower if allowlist/rules grow.  
- **Fix:** Precompile path-prefix allow set; skip file entirely if path allowlisted; apply regex only when needed.  

### BH-009 — find_unclosed_report unbounded (info)

- **Category:** performance  
- **Evidence:** Iterates all `reports/loops/*.md` by mtime, reading each until unclosed lesson found.  
- **Impact:** Long-lived apps with years of loop reports pay more at every session-start compound gate.  
- **Fix:** Cap scan to last N days or last 20 reports; prefer `lessons-state` timestamps.  

### BH-010 — deploy rglob full trees (info)

- **Category:** performance  
- **Evidence:** `collect_paths_from_spec` uses `base.rglob("*")` for each selection directory.  
- **Impact:** Upgrade/init is infrequent; cost dominated by copy/customize. Optimize only if profiling shows pain.  
- **Fix (optional):** Prefer git-tracked files list or bundle manifest file lists over rglob.

## Weaknesses (non-bugs)

| ID | Area | Risk | Recommendation |
|----|------|------|----------------|
| W-1 | `chains/registry.yaml` size | Agent full-file Read wastes tokens | Keep MCP `get_chain_detail`; never full Read in skills |
| W-2 | Efficiency microbench not in CI | Regressions silent | Add optional perf smoke tests under `tests/test_*perf*.py` (skipped unless `PERF=1`) |
| W-3 | No app ORM | N+1 not applicable | When hunting apps, use project-specific specialists |

## Scan artifacts

- `reports/bugs/scan-20260711-efficiency.txt` — generic bug-hunter-scan (few hits; template-shaped)  
- `reports/bugs/efficiency-grep-2026-07-11.txt` — pattern inventory (128 Python/shell files)  
- Microbench (local): vault 50 appends after 500 events ≈ 0.15s; verify_ledger n=550 ≈ 0.004s  
- Tool wall times: malware-lint ≈ 0.42s; skill-governance ≈ 0.10s; bundle-hash verify ≈ 0.04s  

## Handoffs

- **security-audit-agent:** no (efficiency only; malware path already gated)  
- **test-specialist-agent:** yes — vault + token_monitor + MCP cache tests after fixes  
- **project-drift-guardian:** no  
- **git-workflow-guardrails:** when shipping BH-006 (CLI behaviour change)

## Remediation plan (phased)

### Phase A — Quick wins (½–1 day) — **recommended next**

| Order | Finding | Change | Risk |
|------|---------|--------|------|
| A1 | BH-004 | Single-pass `token_monitor` parse | low |
| A2 | BH-005 | Single STATE read in `append_state_lessons` | low |
| A3 | BH-007 | skill-governance default critical-only | low |
| A4 | BH-001 | Tail-window or batch hash set for `append_event` | low–med (correctness tests) |

### Phase B — Scaling correctness (1 day)

| Order | Finding | Change | Risk |
|------|---------|--------|------|
| B1 | BH-002 | `seen_hashes` parent/relation index in `verify_ledger` | low |
| B2 | BH-003 | MCP registry mtime cache + id index | low |
| B3 | BH-009 | Cap unclosed report scan | low |

### Phase C — CLI / CI polish (optional)

| Order | Finding | Change | Risk |
|------|---------|--------|------|
| C1 | BH-006 | Reuse existing upgrade branch | med (gitops semantics) |
| C2 | BH-008 | Allowlist/path short-circuit in malware-lint | low |
| C3 | BH-010 | Only if deploy profiling warrants | low |

### Phase D — Verification

1. `PYTHONPATH=scripts pytest tests/test_vault_workspace_pointer.py tests/test_bundle_hash.py -q`  
2. MCP security tests if BH-003 touched  
3. Microbench script under `scripts/` or `tests/` with `PERF=1`  
4. Update CONCERNS only if residual growth risk remains after Phase B  

### Out of scope this hunt

- App-repo Laravel N+1 / query plans (use per-app hunt)  
- Security malware patterns (already covered by v1.6.1 gates)  
- Style-only refactors  

## Fix log (Phase A)

| Finding | Action | File(s) | Tests | rollback_exempt |
|---------|--------|---------|-------|-----------------|
| BH-001 | fixed — process-local hash-set cache by (path, mtime, size); warm update after append | `scripts/_engine/vault.py` | `test_append_event_*` | false |
| BH-004 | fixed — `parse_session_updates` single-pass; sync/analyze use it | `.grok/skills/token-usage-meter/scripts/token_monitor.py` | `tests/test_token_monitor_parse.py` | false |
| BH-005 | fixed — single STATE read via `_lessons_from_state_text` | `scripts/loop_compound.py` | existing compound import smoke | false |
| BH-007 | fixed — `scan(..., include_info=False)` default; `--info` opt-in | `scripts/orchestrator-skill-governance.py` | `test_default_scan_skips_info_findings` | false |

**Backup ID:** `2026-07-11T122301Z`  
**fixes_applied:** true  

## Fix log (Phase B + C) — 2026-07-11

| Finding | Action | File(s) | Tests |
|---------|--------|---------|-------|
| BH-002 | fixed — `seen_hashes` / `all_hashes` O(n) parent & relation checks | `scripts/_engine/vault.py` | vault tests + live ledger verify |
| BH-003 | fixed — mtime cache + `get_chain_by_id` | `mcp-server/.../helpers.py`, `server.py` | `tests/test_mcp_registry_cache.py` |
| BH-006 | fixed — checkout existing branch or create | `src/orchestrator_cli/gitops.py` | CLI flow smoke |
| BH-008 | fixed — path allowlist skips file before read | `scripts/orchestrator-malware-lint.py` | malware lint clean |
| BH-009 | fixed — scan last 20 non-host reports | `scripts/_engine/app_compound.py` | app_compound tests |
| BH-010 | deferred — deploy rglob infrequent | — | — |

**Bug hunter complete** for planned efficiency work (BH-010 deferred). Release: **v1.7.0**.

## Next actions

1. ~~Phase A–C~~ **done**  
2. Ship **v1.7.0** (merge → master → tag)  
3. Optional later: BH-010 deploy rglob if profiling warrants  

## Handoff (≤80 tokens)

```
bug_hunt: 10 findings; fixed=9; deferred=1 (BH-010); tests=pass
release: v1.7.0
security_pending: none
```
