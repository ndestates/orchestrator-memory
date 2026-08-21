# HTTP cache headers — quick reference

## Cache-Control directives

| Directive | Meaning |
|-----------|---------|
| `public` | Shared caches (CDN) may store |
| `private` | Only browser; not CDN |
| `no-store` | Do not store (sensitive) |
| `no-cache` | May store but must revalidate before use |
| `max-age=N` | Fresh for N seconds (browser) |
| `s-maxage=N` | Fresh for N seconds (**shared**/CDN) |
| `immutable` | Won't change while fresh (hashed assets) |
| `stale-while-revalidate=N` | Serve stale while revalidating |
| `stale-if-error=N` | Serve stale on origin error |
| `must-revalidate` | No stale after max-age without revalidation |

## Recipes

### Hashed Vite/Mix asset (`/build/assets/app-Di3x.js`)

```http
Cache-Control: public, max-age=31536000, immutable
```

### Public marketing HTML (with CDN)

```http
Cache-Control: public, max-age=60, s-maxage=300, stale-while-revalidate=60
```

### Authenticated app page

```http
Cache-Control: private, no-store
```

### Public PDF brochure

```http
Cache-Control: public, max-age=86400
Content-Type: application/pdf
```

### Private user document (via signed URL response)

```http
Cache-Control: private, max-age=300
# Prefer: no CDN shared cache; short-lived signed URL
```

## Validators

- Prefer strong **ETag** for mutable public JSON/HTML when TTL short.
- `If-None-Match` / `If-Modified-Since` → `304 Not Modified`.

## Vary (keep tight)

| Good | Risky |
|------|--------|
| `Accept-Encoding` | `Cookie` on public pages |
| `Accept` for image format negotiation (careful) | `*` |

## Laravel response examples

```php
return response($html)
    ->header('Cache-Control', 'public, max-age=60, s-maxage=300, stale-while-revalidate=60');

return response()->file($path, [
    'Cache-Control' => 'public, max-age=86400',
    'Content-Type' => 'application/pdf',
]);
```

Middleware group idea: `cache.public`, `cache.assets`, `cache.private`.
