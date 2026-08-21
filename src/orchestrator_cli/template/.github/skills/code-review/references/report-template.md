# Code review report template

```markdown
# Code review — YYYY-MM-DD

- **Branch / target:** …
- **Base:** origin/develop | origin/master | HEAD
- **Mode:** standard | deep | pr
- **Stack lens:** php,mysql,python | generic | template
- **Files in diff:** N (list up to 15; then “+K more”)
- **Verdict:** APPROVE | REQUEST_CHANGES | COMMENT

## Intent (context)

<one short paragraph: what the change claims to do>

## Summary

<2–4 sentences: code health impact, dominant risks, whether CI/automation covers style>

## Findings — process / stack

### B1 — blocking: short title
- **File:** path:line
- **Layer:** stack | process | local-orchestrator
- **Why:** …
- **Suggestion:** …

### H1 — high: …
…

## Findings — strict maintainability (existing code-review skill)

**strict_skill:** applied (references/strict-maintainability.md)

### S1 — blocking|high: short title
- **File:** path:line
- **Why:** (code judo / file-size / spaghetti / layer / wrapper …)
- **Suggestion:** …

## Praise (optional)

- …

## What was not reviewed

- Style (deferred to linters/CI)
- Out-of-diff modules
- …

## Follow-ups

- security-audit-agent: yes|no
- bug-hunter deeper: yes|no
- tests required before merge: yes|no

## Cache cited

- manifest, CONVENTIONS, …
```
