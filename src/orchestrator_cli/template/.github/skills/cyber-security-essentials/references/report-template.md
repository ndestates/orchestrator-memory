# Cyber Essentials compliance report — template

**Project:** `<name>`  
**Date:** `YYYY-MM-DD`  
**Scope:** `<module | whole codebase | pre-deploy>`  
**Assessor:** cyber-security-essentials skill  
**Framework:** UK NCSC Cyber Essentials (five controls)

## Executive summary

≤120 words: overall posture, certification readiness (code/config slice), top 3 gaps.

## Control summary

| Control | Code/config status | CE-critical | CE-high | Notes |
|---------|-------------------|-------------|---------|-------|
| 1. Firewalls | pass / partial / fail | n | n | |
| 2. Secure configuration | pass / partial / fail | n | n | |
| 3. User access control | pass / partial / fail | n | n | |
| 4. Malware protection | pass / partial / fail | n | n | |
| 5. Security update management | pass / partial / fail | n | n | |

## Findings

### CE-001 — `<title>`

- **Control:** 1–5
- **Severity:** CE-critical | CE-high | CE-medium | CE-low | CE-info
- **Location:** `path:line` or config file
- **Evidence:** what was observed
- **NCSC requirement:** which control/principle
- **Remediation:** concrete fix (code or process)
- **Out-of-code:** yes/no — if yes, who owns it (infra, ops, board)

(repeat per finding)

## Organisational / infra gaps (out-of-code)

List items certification needs but this skill cannot verify in the repo (firewall appliances, AV on endpoints, asset register, insurance, board sign-off).

## Handoff to other skills

| Finding theme | Delegate to |
|---------------|-------------|
| Auth bypass, policies, consent | security-audit-agent |
| Logic bugs, races, validation | bug-hunter-agent |
| Schema/migration safety | schema-audit-agent |
| Deploy/CI drift | project-drift-guardian |
| AI guardrails maturity | ai-engineering-maturity |

## Cache cited

- `docs/codebase/CONCERNS.md`
- (others)

## Next actions

1. …
2. …