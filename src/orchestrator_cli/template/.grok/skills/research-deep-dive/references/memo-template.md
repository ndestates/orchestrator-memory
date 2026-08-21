# Research memo template

Use for Phase **memo** output at `reports/research/<slug>-YYYY-MM-DD.md`. Replace placeholders; delete unused sections.

```markdown
# Research: <topic title>

**Date:** YYYY-MM-DD  
**Branch:** `<active branch>`  
**Chain:** research-deep-dive | none  
**Status:** draft | ready-for-implementation

## Summary

2–4 sentences: what was researched, recommended direction, biggest risk.

## Success criteria

What "done" looks like before implementation starts (from Phase frame).

## Context (from cache)

- TODO alignment: …
- Manifest / stack constraints: …
- Related cache paths: `docs/codebase/…`, `TODO/…`

## Perspective findings

### Developer
- …

### Operator
- …

### Security
- …

### Product / stakeholder
- …

### Compliance (if used)
- …

## Evidence

| Claim | Source | Tag |
|-------|--------|-----|
| … | cache: `path` | answerable-from-cache |
| … | user-provided: … | user-source |
| … | web (approved): URL | web-approved |

## Options

### Option A — <name>
- **Description:** …
- **Pros:** …
- **Cons:** …
- **Effort:** low | medium | high

### Option B — <name>
…

## Recommendation

**Preferred:** Option …  
**Rationale:** …  
** Preconditions:** …

## Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| … | low/medium/high | … |

## Open questions ([ASK USER])

1. …

## Implementation handoff

Suggested next steps (pick one or more):

- `/orchestrator <task>` — multi-domain implementation plan
- `/<domain-skill>` — e.g. paypal-billing-integration, amazon-ses-email
- `/chain pre-flight` — branch + drift + test-safety before coding

**Memo path:** `reports/research/<slug>-YYYY-MM-DD.md`

## Non-goals (this research)

- Not a STORM/Wikipedia article
- Not codebase onboarding (use `/acquire-codebase-knowledge`)
- Not implementation (no source edits in this chain)
```