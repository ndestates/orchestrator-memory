# Documentation

[UPDATED 2026-07-07]

## Overview

This repository maintains two documentation layers: a **human-navigable site** (`docs/`) and an **agent cache** (`docs/codebase/`). The documentation-specialist skill produces both.

## Before you begin

- Understand [content policy](#content-policy) — no secrets, trade secrets, or coding tips

## Refresh the full doc site

```text
/chain documentation-full
```

Steps: load-cache → read-codebase (optional if cache stale per .codebase-freshness.txt) → readme-specialist → documentation-specialist.

Recent updates include secure vault graph integration (Phase 2.5 outline-first before bodies; Layer B aligns docs/codebase with vault mentions in ARCHITECTURE, CONCERNS).

## Update from current cache only

```text
/chain documentation-refresh
```

Skips full codebase scan.

## Page structure (every guide)

1. Overview
2. Before you begin
3. Numbered steps
4. Verify
5. **Next steps** (required)

Section folders require an `index.md` listing all child pages.

## Content policy

| Include | Exclude |
|---------|---------|
| Procedures, verify steps | API keys, tokens, passwords |
| Chain and skill usage | Trade secrets, proprietary logic |
| Config field names with `YOUR_*` placeholders | Coding tips and clever shortcuts |

Chaining and workflow instructions are in scope.

## Blueprint

Template: `.grok/skills/documentation-specialist/references/doc-site-blueprint.md`

## Verify

- `docs/index.md` links to all sections (hub ≤2 clicks)
- Every page has **Next steps**
- Red-team: no real credentials in markdown
- Full automated link audit: `python3 scripts/docs-link-audit.py --report reports/docs/audit-$(date +%Y-%m-%d).md` (persisted script; 130 internal links, all resolve as of 2026-07-07).

## Next steps

- [Documentation hub](../index.md)
- [Chains and skills](chains-and-skills.md)
- [Knowledge vault](knowledge-vault.md) — for secure self-building updates
- [Skills reference](../reference/skills.md) — `/documentation-specialist` entry

## Related

- [Guides index](index.md)