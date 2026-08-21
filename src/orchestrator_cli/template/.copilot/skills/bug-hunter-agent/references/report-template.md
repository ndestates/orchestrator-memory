# Bug Hunter Report Template

Write to `reports/bugs/YYYY-MM-DD-bug-hunt[-scope].md`.

```markdown
# Bug Hunt Report — [scope or area]

**Date:** YYYY-MM-DD  
**Mode:** scan | deep | pre-deploy | fix (from chain `skill_args` or direct invoke)  
**Branch:** [branch]  
**Backup ID:** [backup_id or n/a — required for fix mode]  
**Rollback:** `python3 .grok/skills/bug-hunter-agent/scripts/bug-hunt-backup.py rollback --backup-id <id>`  
**Cache cited:** [files/sections]

## Executive summary

≤5 bullets: counts by severity, top risks, fix status.

## Findings

| ID | Sev | Cat | Location | Summary | Status |
|----|-----|-----|----------|---------|--------|
| BH-001 | high | logic | path:line | … | open / fixed / suggested |

### BH-001 — [title] (severity)

- **Category:** …
- **Evidence:** code citation or command output
- **Impact:** …
- **Reproduction:** steps or "static analysis"
- **Fix:** applied patch summary OR suggested diff OR "delegate to X"
- **Tests:** added/updated/none (test DB only)

(Repeat per finding.)

## Weaknesses (non-bugs)

| ID | Area | Risk | Recommendation |
|----|------|------|----------------|

## Scan artifacts

- `bug-hunter-scan.sh` output path (if run)
- Commands run (test DB only)

## Handoffs

- security-audit-agent: [yes/no + focus]
- test-specialist-agent: [yes/no + cases]
- project-drift-guardian: [yes/no]

## Next actions

1. …
```

## Fix log (when mode includes fix)

Append to report or `reports/bugs/YYYY-MM-DD-fixes.md`:

| Finding | Action | File(s) | Tests |
|---------|--------|---------|-------|
| BH-00X | fixed / suggested / deferred | path | pass/fail/n/a | rollback_exempt |

- **fixed** — patch applied (low/medium only unless user approved)
- **suggested** — critical/high or `require_approval_for` area — include diff snippet
- **deferred** — handoff to security-audit-agent or test-specialist-agent
- **rollback_exempt** — `true` only for **critical security** fixes (kept on rollback); else `false`

Set chain handoff `fixes_applied: true|false` and `backup_id: <id>` for downstream test steps.