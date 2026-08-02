---
name: loqate-address-integration
description: "Full skill for Loqate (GBG) Address Capture in Laravel app repos."
argument-hint: 'Task (e.g. "add Loqate type-ahead to signer form", "proxy Find/Retrieve API routes", "store retrieved address on Signer model")'
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---
# Loqate Address Capture Integration

**Goal:** Accurate, structured addresses via Loqate Find + Retrieve. HTTPS-only `api.addressy.com`. Non-Microsoft; pairs with Didit (identity) and internal signing flows.

**Canonical facts (mandatory):** Grep then section-read `.grok/skills/loqate-address-integration/references/loqate-api-canonical.md`. **Never invent** query params or response fields. Copy-paste entry: `exports/loqate-integration-prompt.md`.

## Mandatory Start
1. `/load-project-cache-first` — INTEGRATIONS.md, signer/customer models in cache.
2. `/project-drift-guardian` — proxy routes, API key handling.
3. Cross-load: `security-audit-agent` (key exposure), `laravel-expert-agent`, `eval/maintenance-task`.

## App mapping

| App | Typical use |
|-----|-------------|
| **e-ndsign** | Signer address capture on request forms; proof-of-address metadata |
| **ndestates-io** | Checkout/billing address on trial/purchase flows |

**Current wiring:** none in app code — implementation target when skill invoked (`e-ndsign/INTEGRATIONS.md` notes no Loqate yet).

## Procedures (summary)

1. **Key:** `LOQATE_API_KEY` at account.loqate.com (Address Capture service).
2. **Proxy routes:** server-side Find v1.10 + Retrieve v1.20 — key never in frontend.
3. **Type-ahead UX:** debounced Find; handle `Container` with second Find; Retrieve on select.
4. **Persist:** `Line1`, `City`, `PostalCode`, `CountryIso2`, etc. — not temporary Find ids.
5. **Rate limit** proxy; minimal PII retention.

## Laravel pattern

```php
// routes/api.php — throttle + optional auth
Route::middleware('throttle:60,1')->group(function () {
    Route::get('/address/find', [LoqateAddressController::class, 'find']);
    Route::get('/address/retrieve', [LoqateAddressController::class, 'retrieve']);
});
```

Service class wraps Guzzle/curl to canonical endpoints only.

## Security

- API key server-only (DDEV + DO secrets).
- Throttle public find endpoints (enumeration/abuse).
- Do not log full address payloads in production info logs.

## Post-setup

`/eval/maintenance-task --task=loqate-address` · update INTEGRATIONS.md · guardian re-check.

Invoke: `/loqate-address-integration "wire type-ahead on signer create form"`.