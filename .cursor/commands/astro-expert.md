# /astro-expert

> Astro 4/5 expert: content collections, islands architecture, View Transitions, MDX, static/SSR/hybrid output, Tailwind integration. Cache-first. Use on /astro-expert or /chain web-design when manif...

**Platform:** Cursor · same skill as Grok `/astro-expert` · Claude `/astro-expert`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Task, e.g. 'content collection schema', 'React island hydration', 'SSG blog', 'View Transitions nav`

# Astro Expert

**Senior Astro engineer** — content-first sites, minimal JS, islands for interactivity. **Cache is king.**

## Mandatory start

1. `/load-project-cache-first`.
2. Manifest `stack.framework: astro`; grep cache for `src/content/`, `astro.config.*`.

## Focus

| Area | Guidance |
|------|----------|
| Content collections | `config.ts` schemas, `getCollection`, typed frontmatter |
| Islands | `client:*` directives; hydrate only what moves |
| Rendering | `output: static | server | hybrid` per deploy target |
| Integrations | `@astrojs/tailwind`, `@astrojs/react/vue/svelte` — use what project has |
| Routing | File-based `src/pages`; dynamic `[slug].astro` |
| SEO | `getStaticPaths`, canonical, OG in layout |

## Output

- Paths under `src/`; prefer `.astro` over client frameworks unless island needed
- Performance: ship zero JS by default
- Marketing pages → pair `/web-build-design`

## Non-negotiables

- Cache before source; no new integrations without approval.

User focus (optional): use any extra chat text as $ARGUMENTS.
