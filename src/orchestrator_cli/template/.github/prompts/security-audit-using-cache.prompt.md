---
description: "Perform a security audit for this project using the local cache + official checklist script. Use after any dependency change or when adding/changing form input/ rendering/validation code."
name: "Security Audit Using Cache"
argument-hint: "Scope, e.g. 'dependency update', 'new form in PropertyResource', 'full'"
agent: "agent"
tools: ["read_file", "run_in_terminal", "grep_search"]
---

# Security Audit Using Cache (Token-Efficient)

**MANDATORY**: First load the cache via `load-project-cache-first.prompt.md`.

## Required Cache Reads Before Running Checks
- `docs/codebase/CONCERNS.md` (especially items 6 and 7 on Dependabot and phpspreadsheet)
- `docs/codebase/CONVENTIONS.md` (security-first non-negotiables)
- `.github/copilot-instructions.md` section 2 (Mandatory Security Checklist Trigger)

## Execution Steps
1. Confirm the trigger condition from copilot-instructions.md section 2.
2. Run the official script (DDEV):
   ```
   ddev exec ./scripts/ci_security_checklist.sh
   ```
3. Review `reports/security/` artifacts if present.
4. Cross-reference findings against open items in CONCERNS.md.

## Output Format
Return:
- Trigger reason (why this audit was requested)
- Checklist PASS/FAIL summary
- Any high/critical findings with file paths
- Mapping to numbered CONCERNS items (e.g. "Relates to item 7 — phpspreadsheet P1")
- Recommended next actions (do not auto-fix unless explicitly asked)

Always cite the cache files used.
