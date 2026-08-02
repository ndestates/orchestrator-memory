# PayPal purchase wiring — ndestates.io ↔ orchestrator

**Status:** Wire-ready (2026-07-18)  
**Portal repo:** `ndestates-io` branch `feature/orchestrator-pro-paypal-license-2026-07-18`  
**CLI contract:** `POST /api/licenses/validate` (same shape as `orchestrator_cli.license.LicenseGate`)

## Product freeze (commerce)

| SKU | Price | Scope |
|-----|-------|--------|
| Light | Free | No key / anonymous validate |
| Pro monthly | **£99 / month** | One **company** key |
| Pro annual | **£990 / year** | 10× monthly = **2 months free** |

## Portal endpoints (ndestates-io)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/licenses/validate` | CLI / MCP gate |
| POST | `/paypal/orchestrator-pro/start` | Start PayPal (email + interval) |
| GET | `/paypal/return` | Capture/activate → issue key (shown once) |
| GET | `/paypal/cancel` | User cancelled |
| POST | `/webhooks/paypal` | Subscription cancel/renew + capture events |

## Client env after purchase

```bash
export ORCHESTRATOR_LICENSE_URL=https://ndestates.io/api/licenses/validate
# local: https://ndestates-io.ddev.site/api/licenses/validate
export ORCHESTRATOR_LICENSE_KEY=orch_…
orchestrator license
orchestrator upgrade /path/to/app
```

## PayPal operator setup

1. Create PayPal app (sandbox → live).  
2. Create **Product** + **Subscription Plans**:  
   - Monthly £99 GBP → `PAYPAL_PLAN_ORCHESTRATOR_PRO_MONTHLY`  
   - Annual £990 GBP → `PAYPAL_PLAN_ORCHESTRATOR_PRO_ANNUAL`  
3. Webhook URL: `https://ndestates.io/webhooks/paypal`  
   Events: `BILLING.SUBSCRIPTION.*`, `PAYMENT.CAPTURE.COMPLETED`  
4. Env on portal (DO / DDEV):

```env
PAYPAL_MODE=sandbox
PAYPAL_CURRENCY=GBP
PAYPAL_SANDBOX_CLIENT_ID=…
PAYPAL_SANDBOX_CLIENT_SECRET=…
PAYPAL_WEBHOOK_ID=…
PAYPAL_PLAN_ORCHESTRATOR_PRO_MONTHLY=P-…
PAYPAL_PLAN_ORCHESTRATOR_PRO_ANNUAL=P-…
# Local without network:
PAYPAL_MOCK_CHECKOUT=true
```

Without plan IDs, portal falls back to **Orders API** one-time charge for the period (still issues a Pro key).

## Validate JSON (success Pro)

```json
{
  "valid": true,
  "ttl": 2592000,
  "is_first_party": false,
  "tier": "pro",
  "allowed_selections": null,
  "scope": "company",
  "lease_token": "…"
}
```

## Validate JSON (Light / no key)

```json
{
  "valid": true,
  "tier": "trial",
  "allowed_selections": ["grok","chains","loops","scripts","cache-spine"],
  "anonymous_light": true
}
```

## Code map

| Repo | Path |
|------|------|
| ndestates-io | `app/Services/PayPal/*`, `PayPalCommerceService`, `OrchestratorLicenseGateService` |
| ndestates-io | `routes/api.php`, `routes/web.php` (paypal + webhook) |
| orchestrator | `src/orchestrator_cli/license.py`, `defaults.py`, `license_server.py` |

## Not done (next)

- Email delivery of key (Mailpit local / SES prod)  
- Live PayPal plan IDs in production secrets  
- Filament “resend key” / customer portal  
- Default release wheel `ORCHESTRATOR_BUILD_DEFAULT_LICENSE_URL` once DNS is live  
