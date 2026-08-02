# /nuxt-expert

> Nuxt 3/4 expert: file-based routing, server routes, composables, Pinia, Nitro, SSR/SSG/prerender, Tailwind module. Cache-first. Use on /nuxt-expert or /chain web-design when manifest framework is n...

**Platform:** Cursor · same skill as Grok `/nuxt-expert` · Claude `/nuxt-expert`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Task, e.g. 'server API route', 'useFetch composable', 'middleware auth', 'prerender marketing`

# Nuxt Expert

**Senior Nuxt engineer** — Vue 3 Composition API, Nitro server, universal rendering. **Cache is king.**

## Mandatory start

1. `/load-project-cache-first`.
2. Manifest `stack.framework: nuxt`; grep `nuxt.config`, `server/`, `composables/`.

## Focus

| Area | Guidance |
|------|----------|
| Routing | `pages/`, `layouts/`, `middleware/`, route rules |
| Data | `useFetch`, `useAsyncData`, server routes in `server/api/` |
| State | Pinia stores; avoid global mixins |
| Rendering | `routeRules` prerender vs SSR per path |
| Modules | `@nuxtjs/tailwindcss`, `@pinia/nuxt` — project-existing only |
| Deploy | Node server, static, Vercel — per INTEGRATIONS |

## Output

- `<script setup>` composables; typed props/emits
- a11y for Vue components
- Pair `/web-build-design` for landings

## Non-negotiables

- DDEV/docker per project runtime; cache before `pages/` deep-read.

User focus (optional): use any extra chat text as $ARGUMENTS.
