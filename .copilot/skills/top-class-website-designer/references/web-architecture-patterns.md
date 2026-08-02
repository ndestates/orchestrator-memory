# Web Architecture Patterns (CS Perspective)

## Layered / N-Tier
Classic presentation → application → domain → infrastructure. Clear dependency direction. Easy to reason about but can become anemic if domain logic leaks upward.

## Hexagonal (Ports & Adapters)
Domain at center. Ports define interfaces; adapters implement for DB, HTTP, queues. Excellent for testability and swapping MySQL for another store later. Prefer for complex domains.

## CQRS (Command Query Responsibility Segregation) — Light
Separate write models (normalized, transactional) from read models (denormalized views or materialized). Useful when read patterns differ dramatically from write. Combine with MySQL views or secondary tables carefully.

## Event-Driven / Saga
For long-running business processes spanning multiple aggregates or services. Use outbox pattern with MySQL for reliable publishing.

## Progressive Enhancement Stack (Preferred Default)
1. Semantic HTML + server-rendered Jinja
2. HTMX for partial updates and interactivity
3. Alpine.js or small vanilla modules for local state
4. Tailwind for design system
Keeps the majority of logic in Python, improves accessibility and SEO by default, reduces JS surface area and attack surface.

## Complexity Annotations
For any non-trivial endpoint or service method, note:
- Expected time complexity under typical and worst-case data sizes
- Dominant DB operations (index scans vs full table, join cardinality)
- Caching eligibility and invalidation strategy
