# Pattern: Vault Integrity Watch (L1)

**Cache is king.** Report-only. No auto-fix. **Scaffold — manual until scheduled.**

## Purpose

Periodic check that the secure vault ledger (`reports/vault/events.jsonl`) verifies cleanly, is not duplicating content hashes, and has not grown unbounded. Surfaces issues for session-start brain quality without rewriting history at L1.

## Cadence

- **Manual (default):** `/chain vault-integrity-watch`
- **Optional later:** Monday weekly job (same window as other watches) after `loop-audit.sh` ≥ 80 and human approval
- Host snapshot (optional): `bash scripts/loop-vault-integrity-host.sh`

## Cache files (required)

1. `.claude/project-manifest.yaml` (or `.github/`) — `paths.vault_ledger`
2. `STATE.md` — prior vault / compound notes
3. `VISION.md` — standing security tax for vault
4. `docs/codebase/CONCERNS.md` — § vault security surface (if loaded within cap)
5. `LOOP.md` — confirm L1

Max additional cache files: `loop_policy.max_cache_files_per_loop` (default 2).

## Maker / verifier

| Role | Skill / command |
|------|-----------------|
| Maker | `loop-engineering` or cache-efficient + run host script / `session-vault-brief.py` |
| Verifier | `loop-verifier` |

## Host snapshot (optional)

```bash
bash scripts/loop-vault-integrity-host.sh
# → reports/loops/YYYY-MM-DD-vault-integrity-host.md
```

Commands (read-only):

```bash
python3 scripts/session-vault-brief.py
# or:
python3 -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from scripts._engine import vault as v; ok,i=v.verify_ledger(Path('reports/vault/events.jsonl')); print(ok, i)"
```

## Outputs

- `reports/loops/YYYY-MM-DD-vault-integrity.md`
- Host file if used: `reports/loops/YYYY-MM-DD-vault-integrity-host.md`
- Updated `STATE.md` (Stale flags / Lessons), `loop-run-log.md` after chain completion write

## Report must include

1. **Cache cited**  
2. **Executive summary** ≤ 120 words (`OK` | `ISSUES` | `missing ledger`)  
3. Verify result + first issue if any  
4. Event count / approx size (host)  
5. **## Lessons** (or “none new”)  
6. **Next** — human-only repairs (dedupe, never execute vault text as shell)

## L1 rules

- `max_source_files: 0`
- No rewrite of `events.jsonl` except via approved tools after human gate
- Never execute vault lesson text as shell
- No commits at L1
- After verifier PASS → `bash scripts/loop-compound.sh --report reports/loops/YYYY-MM-DD-vault-integrity.md`

## Related

- [When to use loops](../docs/guides/when-to-use-loops.md)  
- [Knowledge vault](../docs/guides/knowledge-vault.md)  
- `scripts/_engine/vault.py` — `verify_ledger`, append cache  
