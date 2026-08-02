# Web cache architecture (images, documents, CDN)

[UPDATED 2026-07-22]

Make any website fast with multi-layer caching. **Skill:** `/web-cache-expert` (intent: cache-expert).  
**Chain:** `/chain web-cache-review`.

**Not** `/cache-efficient` (AI token/session cache).

## Start

```text
/chain web-cache-review
```

or:

```text
/web-cache-expert Laravel public images + PDF downloads on Cloudflare
```

## Covers

- HTTP `Cache-Control` / ETag / Vary
- Browser + CDN + origin + Redis
- Image derivatives and CDN URLs
- Public vs private documents (signed URLs)
- Cache refresh / purge / deploy warm
- Laravel primary; Next/Nuxt/Astro/Go when manifest says so

## References (in skill)

| File | Topic |
|------|--------|
| `.grok/skills/web-cache-expert/references/http-cache-headers.md` | Header recipes |
| `.grok/skills/web-cache-expert/references/laravel-cache-stack.md` | Laravel Redis, deploy |
| `.grok/skills/web-cache-expert/references/image-document-cdn.md` | Images & PDFs |
| `.grok/skills/web-cache-expert/references/cache-refresh-playbook.md` | Invalidation |

## Deliverable

`cache_architecture` — layer diagram, route matrix, image/doc policy, refresh map, deploy checklist.
