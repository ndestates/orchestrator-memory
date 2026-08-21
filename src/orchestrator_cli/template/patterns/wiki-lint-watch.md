# Pattern: Wiki Lint Watch (L1)

**Cache is king.** Report-only. No auto-fix. **Scaffold — manual until scheduled.**

## Purpose

Periodic health check of the LLM wiki (`wiki/`): log format, broken links, missing frontmatter sources, scaffold completeness. Surfaces gaps for `/chain wiki-lint` follow-up without rewriting pages at L1.

## Cadence

- **Manual (default):** `/chain wiki-lint-watch`
- **Optional later:** Monday weekly job after `loop-audit.sh` ≥ 80 and human approval
- Host snapshot: `bash scripts/loop-wiki-lint-host.sh`

## Cache files (required)

1. Manifest — `wiki_policy`, `paths.wiki_*`
2. `wiki/index.md`, `wiki/log.md` (when mode ≠ off)
3. `STATE.md` / `LOOP.md` — L1 confirmation

Max additional: `loop_policy.max_cache_files_per_loop` (default 2).

## Maker / verifier

| Role | Skill / command |
|------|-----------------|
| Maker | `llm-wiki` lint + host script |
| Verifier | `loop-verifier` |

## Host snapshot

```bash
bash scripts/loop-wiki-lint-host.sh
# → reports/loops/YYYY-MM-DD-wiki-lint-host.md
python3 scripts/wiki_lint_check.py --json
```

## Outputs

- `reports/loops/YYYY-MM-DD-wiki-lint.md` (agent report)
- Host: `reports/loops/YYYY-MM-DD-wiki-lint-host.md`
- `STATE.md` / `loop-run-log.md` after chain completion write

## Report must include

1. **Cache cited**
2. Executive summary (`ok` | `warn` | `fail` | `skip`)
3. Finding list (level + message)
4. **## Lessons**
5. **Next** — human-approved fixes only

## L1 rules

- `max_source_files: 0` for app code
- No multi-file wiki apply without approval
- No commits at L1
- After verifier PASS → `loop-compound` when useful

## Related

- `/llm-wiki`, chains `wiki-lint`, `wiki-lint-watch`
- `docs/guides/llm-wiki.md`
- `reports/research/llm-wiki-karpathy-plan.md`
