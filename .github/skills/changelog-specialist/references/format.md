# Changelog format (orchestrator template / forked projects)

## Files

| Path | Purpose |
|------|---------|
| `CHANGELOG.md` | Project changelog — `[Unreleased]` until release tag |
| `reports/changelog/session-YYYY-MM-DD.md` | Append-only session log (human-readable) |
| `reports/changelog/state.json` | Machine-readable session entries |
| `reports/changelog/pr-<branch-slug>.md` | PR body generated at EOD |

## Categories

Use Keep a Changelog headings (lowercase in script, Title Case in markdown):

- `added` — new features, files, endpoints, seeders
- `changed` — behaviour or UX changes without fixing bugs
- `fixed` — bug fixes
- `removed` — deleted features or deprecated paths
- `security` — vulnerability or hardening fixes
- `tests` — new or updated test files only
- `infrastructure` — orchestrator, CI, scripts, backups, skills (no app behaviour)

## Entry rules

1. **One line per bullet** — imperative mood, past tense optional; include class/file names in backticks when helpful.
2. **After every substantive action** — commit, feature slice, fix, test add, skill/chain change.
3. **Skip** — trivial acks, read-only Q&A, cache loads, failed attempts that were reverted.
4. **Dedup** — `consolidate` skips bullets already in `[Unreleased]` (normalized match).

## Examples

```bash
python3 .grok/skills/changelog-specialist/scripts/changelog_update.py append \
  --category added --summary "cache-freshness-check skill and checker script" \
  --commit 59fdded5 --files .grok/skills/cache-freshness-check/SKILL.md

python3 .grok/skills/changelog-specialist/scripts/changelog_update.py append \
  --category infrastructure --summary "changelog-specialist skill wired into session-start and eod-shutdown"
```