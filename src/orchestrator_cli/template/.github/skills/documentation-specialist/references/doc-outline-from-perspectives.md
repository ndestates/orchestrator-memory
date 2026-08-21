# Doc Outline from Perspectives — Phase 2.5

Outline-first doc site planning (STORM-inspired pattern; **not** STORM). Run after cache load (Phase 0) and chain handoffs (Phase 2), **before** writing any `docs/**/*.md` page bodies.

## Inputs

- `docs/codebase/README.md`, latest cache files, `TODO/`, manifest `stack` + `paths`
- Optional: `reports/codebase/.perspective-pass.md` if `acquire-codebase-knowledge` ran in the same chain
- User scope: `full` | `refresh` | `architecture` | `onboarding` | `api` | `integrations`

## Audience lenses (map to pages)

| Lens | Typical pages |
|------|---------------|
| **Developer** | quickstart, local-runtime, conventions, testing |
| **Operator** | delivery, deploy, CI gates, runbooks |
| **Security** | operations/testing (safety), reference/manifest (policy fields) |
| **Product / onboarding** | project-overview, getting-started hub, guides/daily-workflow |
| **Compliance** (optional) | operations runbooks, api reference — when app has regulated flows |

## Outline template (emit before Layer A writes)

Save optional draft: `reports/docs/.doc-outline-YYYY-MM-DD.md`

```markdown
# Documentation outline — YYYY-MM-DD

**Scope:** full | refresh | …
**Repo class:** template | app fork
**Chain:** <id or none>

## Hub
- `docs/index.md` — primary audiences: …

## Section: getting-started/
| Page | Primary lens | Prerequisites | Verify step | Status |
|------|--------------|---------------|-------------|--------|
| index.md | Product | none | Links to quickstart + overview | write |
| quickstart.md | Developer | manifest paths | User can run start command | write |
| project-overview.md | Product | cache README | Matches TODO stated purpose | write |

## Section: guides/
| Page | Primary lens | Prerequisites | Verify step | Status |
|------|--------------|---------------|-------------|--------|
| … | … | … | … | write \| skip \| [ASK USER] |

## Section: reference/
…

## Section: operations/
…

## App-only extensions (if applicable)
- guides/local-runtime.md — …
- operations/deploy.md — …

## Cache cross-links (Layer B)
| Cache file | Human page(s) |
|------------|---------------|
| docs/codebase/ARCHITECTURE.md | guides/…, reference/… |

## Pages blocked ([ASK USER])
1. …

## Cross-lens conflicts
- …
```

### Status values

| Status | Meaning |
|--------|---------|
| `write` | Proceed in Layer A |
| `skip` | Exists and fresh — link only |
| `refresh` | Exists but stale — update in place |
| `[ASK USER]` | Do not write until user answers |

## Rules

1. **Outline before bodies** — no new `docs/**/*.md` content until this table exists (except updating `[UPDATED]` on skipped pages).
2. **Full scope** — include all sections from [doc-site-blueprint.md](doc-site-blueprint.md); mark `skip` where already complete.
3. **Refresh / targeted scope** — outline only touched sections + hub links.
4. **Max 20 open `[ASK USER]` page blocks** — prefer marking specific sections, not whole site.
5. **No secrets** in outline — reference config field names only.

## Layer A execution

Write pages **in outline table order**. Each page must include:

- Overview (name primary lens audience)
- Before you begin (prerequisites from outline)
- Numbered steps
- Verify (from outline)
- Next steps (2–3 relative links)

## Layer B execution

Update `docs/codebase/*` only to align with Layer A — cross-link human pages; avoid duplicating full prose. Add to `docs/codebase/README.md` index when new human sections appear.

## Chain handoff extension

When chaining, extend Phase 2 JSON handoff:

```json
{"doc_scope":"full","outline_ready":true,"blocked_pages":0,"primary_lenses":["developer","operator"]}
```

If `read-codebase` ran earlier in chain, prefer reusing `reports/codebase/.perspective-pass.md` for conflict notes.