# Image & document CDN patterns

## Image URL design

Good (cache forever, change URL on edit):

```text
https://cdn.example.com/img/{hash}/w_800,h_600,f_webp/photo.jpg
https://cdn.example.com/media/properties/123/hero.v3.800.webp
```

Bad (always hit origin, no variant key):

```text
https://app.example.com/resize.php?src=/uploads/photo.jpg&w=800
```

## Pipeline

```text
Upload → store original (private or public bucket)
      → enqueue derivatives (sizes × formats)
      → write to object storage
      → CDN in front of bucket (or image CDN)
```

| Size | Typical use |
|------|-------------|
| thumb | lists, cards |
| card | grid |
| hero | LCP (one priority image) |
| full | lightbox / zoom |

## Document classes

| Class | Storage | CDN | URL |
|-------|---------|-----|-----|
| Marketing PDF | public bucket | yes | stable or versioned name |
| Listing brochure | public or signed | yes if public | version on update |
| KYC / contracts | private bucket | no shared cache | short-lived signed URL |
| User export | private + short TTL | no | one-time or minutes |

## Cloudflare / generic CDN tips

- Cache Everything only for pure static or known-safe HTML.
- Bypass cache for `/admin`, `/livewire`, authenticated cookies when needed.
- Separate hostname for assets (`cdn.` / `static.`) simplifies rules.
- Origin Cache-Control respected when "Respect Existing Headers" is on.

## Stampede control

- Soft TTL + background revalidate.
- Lock around regenerate (Redis lock) when building derivatives.
- Origin shield / tiered cache on large CDNs.
