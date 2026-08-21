# Bug Hunt Fix — Rollback

**Mandatory** in `fix` mode and all `bug-hunt-*-fix` chains. No fix without a backup session.

## When rollback applies

| Fix type | Backed up | On rollback |
|----------|-----------|-------------|
| Low/medium patch | Yes | Restored to pre-fix content |
| New file created by fix | Tracked | Deleted |
| **Critical security fix** | Yes | **Kept** — exempt from rollback |
| Suggested-only (not applied) | N/A | N/A |

## Critical security exempt

A fix is **rollback-exempt** when **all** are true:

1. Severity **critical**
2. Category is security-related (`security`, `security surface`, `authorization`, `auth`, `injection`, `secrets`)
3. Fix was applied (not suggest-only)
4. Documented in report with `rollback_exempt: true`

Examples: SQL injection patch, auth bypass closure, exposed secret removal.

Non-exempt critical (logic/data bugs) **can** be rolled back — only **security** critical fixes are kept.

## Workflow (agent)

```bash
# 1. Start session before any patch
BACKUP_ID=$(python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py init --scope "auth module" --mode fix)

# 2. Before each file write
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py backup --backup-id "$BACKUP_ID" path/to/file.php

# 3. After critical security fix
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py mark-exempt --backup-id "$BACKUP_ID" \
  --finding-id BH-003 --reason "critical_security_fix" app/Http/Middleware/Auth.php

# 4. New file during fix
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py mark-created --backup-id "$BACKUP_ID" tests/Feature/AuthTest.php

# 5. After report written
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py finalize --backup-id "$BACKUP_ID" \
  --report reports/bugs/2026-06-17-bug-hunt-auth.md
```

## Rollback (human or agent)

```bash
# List
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py list

# Preview
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id 2026-06-17T120000Z --dry-run

# Execute (restores all except critical security exempt)
python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id 2026-06-17T120000Z
```

Backup location: `reports/bugs/backups/<backup_id>/`

## Report fields

Include in fix report header:

- `backup_id: <id>`
- `rollback_cmd: python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id <id>`
- Per fixed finding: `rollback_exempt: true|false`