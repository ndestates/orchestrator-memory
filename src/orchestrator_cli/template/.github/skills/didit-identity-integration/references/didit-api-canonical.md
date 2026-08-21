# Didit API — Canonical Reference (ground truth)

```yaml
vendor: didit
api_version: v3
last_verified: 2026-06-19
sources:
  - https://docs.didit.me/integration/integration-prompt
  - https://docs.didit.me/llms.txt
  - https://docs.didit.me/openapi-25.json
  - https://docs.didit.me/openapi-auth.json
```

**Anti-hallucination:** Use only endpoints, fields, status strings, and headers listed here. If missing, fetch `sources` above — never invent params or response keys.

## Base URLs

| Surface | Base URL |
|---------|----------|
| Verification API (`/v3/...`) | `https://verification.didit.me` |
| Auth / account (`/auth/v2/...`) | `https://apx.didit.me` |
| Console (human) | `https://business.didit.me` |
| Hosted verification UI | `https://verify.didit.me` |
| Docs | `https://docs.didit.me` |

## Auth (programmatic account)

```bash
# Register — 201; emails 6-char code (10 min TTL). Real inbox required (no @example.com).
curl -X POST https://apx.didit.me/auth/v2/programmatic/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "'"$DIDIT_REGISTER_EMAIL"'", "password": "'"$DIDIT_REGISTER_PASSWORD"'"}'

# Verify email — 200; persist application.api_key as DIDIT_API_KEY
curl -X POST https://apx.didit.me/auth/v2/programmatic/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "'"$DIDIT_REGISTER_EMAIL"'", "code": "'"$DIDIT_EMAIL_VERIFY_CODE"'"}'
```

All verification API calls: header `x-api-key: $DIDIT_API_KEY`.

**Auth errors (session/workflow/standalone):** missing/wrong key → **403** with `{"detail": "You do not have permission to perform this action."}` (not 401). Management families (`/v3/users/`, `/v3/businesses/`, `/v3/billing/`, `/v3/webhook/destinations/`) use **401** for bad key, **403** for permission.

## Integration approaches (pick exactly one)

- **A — Sessions + SDK (default):** backend `POST /v3/session/` → frontend SDK/iframe/redirect → webhook decision.
- **B — Standalone APIs:** server-to-server module calls (`/v3/id-verification/`, `/v3/aml/`, etc.) for batch/custom UI.

## Workflow create (required fields only)

```bash
curl -X POST https://verification.didit.me/v3/workflows/ \
  -H "x-api-key: $DIDIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_label": "Standard KYC",
    "features": [
      {"feature": "OCR"},
      {"feature": "LIVENESS", "config": {"face_liveness_method": "PASSIVE"}},
      {"feature": "FACE_MATCH"},
      {"feature": "IP_ANALYSIS"}
    ]
  }'
```

- **Required:** `workflow_label`, `features[]` with `{ "feature": "UPPERCASE_ENUM", "config": {} }`.
- **No** `workflow_type` field — unknown body fields → **400**.
- KYB: include `KYB_REGISTRY`, `KYB_DOCUMENTS`, or `KYB_KEY_PEOPLE` in features (separate workflows from KYC).
- Save `workflow_id` / `uuid` as `DIDIT_WORKFLOW_ID`.

## Session create (201 — exactly 10 keys)

```bash
curl -X POST https://verification.didit.me/v3/session/ \
  -H "x-api-key: $DIDIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "'"$DIDIT_WORKFLOW_ID"'",
    "vendor_data": "internal-user-id",
    "callback": "https://myapp.com/done"
  }'
```

Response keys: `session_id`, `session_number`, `session_token`, `url`, `vendor_data`, `metadata`, `status`, `workflow_id`, `workflow_version`, `callback`.

- `session_token` = 12-char secret (not JWT). Treat as secret.
- `vendor_data` = your internal user/signer ID.
- Idempotent reuse: unfinished sessions with same `vendor_data` on latest workflow version return existing session (201).

## Webhook destination (register once)

```bash
curl -X POST https://verification.didit.me/v3/webhook/destinations/ \
  -H "x-api-key: $DIDIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Production session webhooks",
    "url": "https://myapp.com/api/webhooks/didit",
    "webhook_version": "v3",
    "subscribed_events": ["status.updated", "data.updated"]
  }'
```

Persist `secret_shared_key` as `DIDIT_WEBHOOK_SECRET` immediately. `(application, url)` must be unique.

**Verify:** `X-Signature-V2` (recommended) — HMAC-SHA256 over `JSON.stringify(sortKeys(shortenFloats(parsed_body)))`. Reject if `abs(now - X-Timestamp) > 300`. Constant-time compare. Dedupe on stable `event_id`.

**Egress IP allowlist:** `18.203.201.92` (User-Agent `DiditWebhook/2.0 +https://didit.me`).

## Session status strings (case-sensitive)

`"Not Started"`, `"In Progress"`, `"Awaiting User"`, `"In Review"`, `"Approved"`, `"Declined"`, `"Resubmitted"`, `"Abandoned"`, `"Expired"`, `"Kyc Expired"`.

## Webhook envelope (v3) — key fields

`event_id`, `webhook_type`, `timestamp`, `session_id`, `status`, `workflow_id`, `vendor_data`, `metadata`, `environment` (`live`|`sandbox`), `decision` (on terminal statuses).

V3 uses **plural arrays** in `decision` (`id_verifications[]`, `liveness_checks[]`, etc.) indexed by `node_id`. Do not use legacy V2 singular keys unless destination pinned to `webhook_version: "v2"`.

## SDK packages

| Stack | Package |
|-------|---------|
| Web | `@didit-protocol/sdk-web` |
| iOS | SPM `https://github.com/didit-protocol/sdk-ios` |
| Android | `me.didit:didit-sdk` |
| React Native | `@didit-protocol/sdk-react-native` |
| Flutter | `didit_sdk` |

## Env vars (allowlist)

`DIDIT_API_KEY`, `DIDIT_WORKFLOW_ID`, `DIDIT_WEBHOOK_SECRET`, `DIDIT_ENVIRONMENT` (`sandbox`|`live`). Registration-only (not runtime): `DIDIT_REGISTER_EMAIL`, `DIDIT_REGISTER_PASSWORD`, `DIDIT_EMAIL_VERIFY_CODE`.