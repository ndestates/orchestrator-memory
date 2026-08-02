> **SUPERSEDED 2026-08-01:** Public product is Apache-2.0 freeware + optional Patreon. See docs/reference/licensing.md.

# Freemium product freeze (v1)

**Date:** 2026-07-18  
**Branch:** `feature/freemium-license-publish-2026-07-18`  
**Status:** Frozen for implementation  

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **License scope** | **One license key per company (organization)** | Simple B2B v1; seats share one key; no seat metering yet |
| **Pro fee** | **£99 per month** per company | Recurring SaaS |
| **Annual** | **Pay 10 months, get 12** (2 months free) | £990/year vs £1,188 monthly |
| **Light price** | Free | Growth + eval without payment |
| **Packaging** | One public package (npm + pip); Pro unlock via key | Plan option A |
| **Enforcement** | `init` / `upgrade` selection caps only | Offline-friendly; not every skill run |
| **Wave** | Neither tier | Deleted permanently |
| **Seat SKU** | Deferred | Optional later `seat` scope |

## Pricing table

| Plan | Billing | Price (GBP) | Included |
|------|---------|-------------|----------|
| **Light** | — | Free | Light selections only |
| **Pro monthly** | Monthly | **£99 / month** | Full selections; company key |
| **Pro annual** | Yearly | **£990 / year** | 12 months access for 10× monthly (2 months free) |

Annual math: `99 × 10 = 990` (not `99 × 12`).

## Light selections (free)

Canonical string (`orchestrator_cli.defaults.LIGHT_SELECTIONS`):

```text
grok,chains,loops,scripts,cache-spine
```

Aliases accepted by deploy: `light`, `trial`, `free`.

### Included

| Selection | Why |
|-----------|-----|
| `grok` | Core skills / session-start path |
| `chains` | Chain registry |
| `loops` | Loop spine |
| `scripts` | Per-app tooling (no fleet) |
| `cache-spine` | Lean docs/codebase cache |

### Pro-only (requires company Pro key)

| Selection | Why |
|-----------|-----|
| `mcp` | Enterprise MCP package |
| `wiki` | LLM wiki deploy |
| `claude` / `copilot` / `github` / `gemini` | Full platform mirrors |
| `loops-starter` | Extra loop automation delta |
| `--selections all` | Unlocks everything in bundle |

## UX mapping

| Server / enum | User-facing |
|---------------|-------------|
| `TRIAL_LITE` / `tier=trial` | **Light** (free) |
| `PRO_FULL` / `tier=pro` | **Pro** (£99/mo company; annual option) |
| First-party remote / key | Full (ND Estates) |

## Client behaviour

| Condition | Entitlement |
|-----------|-------------|
| Dev template / `ORCHESTRATOR_LICENSE_DEV=1` | Open (dev) |
| First-party git remote | Full |
| Gate off / no URL | **Light** (not full open for third-party) |
| Gate on, no key | **Light** (no network) |
| Gate on, valid Pro key | **Pro** |
| Gate on, invalid/revoked key | Denied |

## Commerce (PayPal on ndestates.io)

**Wired in portal repo** (`ndestates-io`): see `docs/internal/PAYPAL-NDESTATES-IO-WIRING.md`.

1. PayPal Subscription / Orders: **£99/month** and **£990/year** (10× monthly)  
2. Webhook → issue/renew/revoke Pro company keys  
3. Validate: `https://ndestates.io/api/licenses/validate`  
4. Still open: production plan IDs + email delivery of keys

## Code anchors

- `src/orchestrator_cli/defaults.py` — `LIGHT_SELECTIONS`, `LICENSE_SCOPE=company`, pricing constants  
- `src/orchestrator_cli/licensing_policy.py` — evaluate/enforce  
- `src/orchestrator_cli/license_server.py` — validate/issue/revoke + SQLite  
- `services/license-api/` — DO Dockerfile + app.yaml  
