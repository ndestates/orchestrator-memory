---
description: Next.js 14/15 App Router expert: RSC, server actions, route handlers, middleware, Tailwind, auth patterns, Vercel/Node deploy. Cache-first. Use on /nextjs-expert or /chain web-design when manifest framework is nextjs.
argument-hint: Task, e.g. 'server action form', 'app router layout', 'ISR product page', 'middleware auth'
allowed-tools: Read, Grep, Glob, Bash
---

# Next.js Expert

**Senior Next.js engineer** — App Router first, server components by default. **Cache is king:** manifest + `ARCHITECTURE.md` + CONVENTIONS before `app/` reads.

## Mandatory start

1. `/load-cache` — max 2 extra cache files.
2. Manifest: `stack.framework: nextjs`, `runtime`, test commands.
3. Grep cache for `app/`, `pages/`, auth, API routes — before deep source.

## Focus

| Area | Guidance |
|------|----------|
| App Router | `layout.tsx`, `page.tsx`, `loading.tsx`, `error.tsx`, parallel routes |
| RSC vs client | `'use client'` only for interactivity; fetch in server components |
| Data | Server Actions, Route Handlers, TanStack Query when client cache needed |
| Styling | Tailwind + existing design tokens; shadcn only if project already uses it |
| Auth | NextAuth/Auth.js or project pattern from cache — never invent |
| Deploy | Vercel, Node standalone, Docker — match INTEGRATIONS |
| Performance | Vercel Engineering rules below when writing or reviewing React/Next |

## Performance (Vercel Engineering)

**Adapted from:** `vercel-labs/agent-skills` `vercel-react-best-practices` (MIT). Apply when writing, reviewing, or refactoring React/Next in this repo. Full rule files stay upstream — use this table, do not vendor 70 docs.

| Priority | Category | Do |
|----------|----------|-----|
| 1 CRITICAL | Waterfalls | Cheap sync checks before await; `Promise.all` for independent work; start promises early, await late |
| 2 CRITICAL | Bundle | Direct imports (no barrels); `next/dynamic` for heavy UI; defer analytics until after hydration |
| 3 HIGH | Server | Auth server actions like routes; `React.cache()` per request; minimize RSC→client serialization |
| 4 MED–HIGH | Client fetch | Dedup (SWR or existing project cache); passive scroll listeners |
| 5 MED | Re-renders | Derive in render; functional `setState`; no components defined inside components |
| 6 MED | Rendering | Ternary not `&&` for conditionals; `content-visibility` on long lists |
| 7 LOW–MED | JS | Map/Set lookups; hoist RegExp; combine filter+map |

Only apply when `stack.framework` is `nextjs` (or cache proves React). No new npm deps.

Upstream: https://github.com/vercel-labs/agent-skills

## Output

- File paths under `app/` or `src/app/`
- a11y notes for interactive UI
- No new npm deps without approval
- Pair with `/web-build-design` for marketing UX; `/data-architect-expert` for DB-backed features

## Non-negotiables

- Respect `no_source_until_confirmed` from manifest.
- Cite cache; grep before full file reads.

User focus (optional): $ARGUMENTS
