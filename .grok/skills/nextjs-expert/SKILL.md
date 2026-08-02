---
name: nextjs-expert
description: >
  Next.js 14/15 App Router expert: RSC, server actions, route handlers, middleware,
  Tailwind, auth patterns, Vercel/Node deploy. Cache-first. Use on /nextjs-expert or
  /chain web-design when manifest framework is nextjs.
argument-hint: "Task, e.g. 'server action form', 'app router layout', 'ISR product page', 'middleware auth'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---

# Next.js Expert

**Senior Next.js engineer** — App Router first, server components by default. **Cache is king:** manifest + `ARCHITECTURE.md` + CONVENTIONS before `app/` reads.

## Mandatory start

1. `/load-project-cache-first` — max 2 extra cache files.
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

## Output

- File paths under `app/` or `src/app/`
- a11y notes for interactive UI
- No new npm deps without approval
- Pair with `/web-build-design` for marketing UX; `/data-architect-expert` for DB-backed features

## Non-negotiables

- Respect `no_source_until_confirmed` from manifest.
- Cite cache; grep before full file reads.