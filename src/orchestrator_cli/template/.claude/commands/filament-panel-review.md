---
description: Review one or more Filament panels/resources in the project project (marketing + customer portal + license server: Admin, Products, Licenses, Customers, Orders, Downloads panels) using the local cache first. Use for panel audits, resource reviews, widget composition checks, or cross-panel reuse analysis.
argument-hint: Panel name or scope, e.g. 'admin', 'block-manager', 'all panels', 'user + lettings', 'sales'
allowed-tools: Read, Grep, Glob, Bash
---

# Filament Panel Review (Cache-First)

**Always start by loading the cache** (see `load-project-cache-first.md`).

## Required First Reads from Cache
1. `docs/codebase/STRUCTURE.md` — Panel table and provider locations.
2. `docs/codebase/ARCHITECTURE.md` — Multi-panel architecture section + cross-panel reuse notes.
3. `docs/codebase/CONCERNS.md` — Any open panel-related items.
4. `.copilot/memories/INDEX.md` + relevant memories.

## Then Read the Specific Panel Provider(s)
- Admin (default): `app/Providers/Filament/AdminPanelProvider.php`
- (Future panels as site grows: e.g. Customer, License, or Reports panels. Public marketing uses Livewire/Blade, not additional Filament panels initially.)

## Review Checklist (cite cache file + line when answering)
- Panel registration and middleware
- Resource discovery / explicit registration
- Widget composition (especially admin dashboard)
- Navigation groups and icons
- Cross-panel resource reuse (e.g. Property, Block, User)
- Any custom theme or render hooks
- Policy / authorization surface

After review, return a structured summary with:
- Panel purpose (1 sentence)
- Resource count and notable resources
- Any deviations from conventions in CONVENTIONS.md
- Recommendations (if any)

Cite specific cache files (e.g. "Per STRUCTURE.md panel table...").

Follow `CLAUDE.md` security and DDEV rules.

User focus (optional): $ARGUMENTS
