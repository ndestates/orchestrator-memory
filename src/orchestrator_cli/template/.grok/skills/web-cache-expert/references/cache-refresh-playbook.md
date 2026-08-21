# Cache refresh playbook

## Principles

1. Prefer **new URL** over purge (hash/version).
2. Purge **narrowly** (path, tag, surrogate key).
3. **Warm** critical paths after purge.
4. Log purges (who, why, scope).

## Triggers

| Event | Action |
|-------|--------|
| Asset deploy | No purge if hashed; else purge `/build/*` or CSS/JS prefixes |
| CMS/page publish | Purge page URL + related list pages |
| Image replace | Purge derivative prefix for that media id; or bump version in URL |
| Price/stock update | Purge product/listing tags; short TTL on price fragments |
| User permission change | Invalidate private signed URLs (short TTL already) |
| Emergency bad content | Targeted URL purge; avoid global |

## Laravel hooks (sketch)

```php
// Model observer
static::saved(function (Property $p) {
    Cache::tags(["property:{$p->id}", 'property-lists'])->flush();
    // dispatch CDN purge job for routes that embed this property
});
```

## CDN purge job

- Queue async; retry with backoff.
- Idempotent; batch URLs.
- Never call CDN purge in HTTP request cycle for bulk admin saves (debounce).

## Deploy CI snippet (conceptual)

```text
build assets → deploy → artisan optimize → migrate →
  purge CDN: / , /properties/* (if HTML cached) →
  warm: homepage, top 20 listings
```

## Health checks

- Random public URL: expect hit ratio rise after warm.
- Authenticated URL: must not be served from shared cache.
- After image update: new derivative visible within SLA (TTL or purge).
