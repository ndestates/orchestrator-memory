# Laravel cache stack

## Drivers

| Driver | Use |
|--------|-----|
| `redis` | Production multi-node default |
| `file` | Single-node / local only |
| `array` | Tests |
| `database` | Avoid for hot paths |

`config/cache.php` + `CACHE_STORE` / `CACHE_DRIVER`. Prefer **tagged** cache (Redis) for model-level invalidation.

## What to cache

| Kind | API | Notes |
|------|-----|-------|
| Config/routes/views | `artisan * :cache` | Deploy only |
| Query/result | `Cache::remember($key, $ttl, fn)` | Key includes tenant/locale |
| Fragments | Blade `@cache` / view composers + Cache | Short TTL |
| Full page | Middleware | Public only; key = path + locale + currency if needed |
| Rate limits | Redis | Not content cache |

## Invalidation

```php
// Prefer tags when available
Cache::tags(['property', "property:{$id}"])->flush();

// Event / observer on saved/deleted
```

Avoid global `Cache::flush()` in production jobs.

## HTTP layer (Laravel)

- Route middleware for `Cache-Control` by group (`web`, `marketing`, `api`).
- Filament/admin: `private, no-store`.
- API personal endpoints: no shared CDN.

## Files & images

| Approach | When |
|----------|------|
| `php artisan storage:link` + local disk | Dev / small |
| S3/DO Spaces + CDN domain | Production assets |
| Glide / Spatie Media Library conversions | Derivatives on disk or S3 |
| CDN image resizing | Offload CPU from PHP |

## Deploy sequence (safe)

1. Build frontend (`npm run build`) — hashed assets.
2. Deploy code.
3. `config:cache` `route:cache` `view:cache` `event:cache` (as used).
4. Migrate.
5. **Selective** Redis tag purge / CDN purge for changed prefixes.
6. Optional warm: hit top public URLs.

Do not clear entire Redis unless emergency.

## Multi-node / Octane

- Shared Redis mandatory for cache and sessions if sticky sessions absent.
- Octane: do not rely on in-process static caches across workers without Redis.
