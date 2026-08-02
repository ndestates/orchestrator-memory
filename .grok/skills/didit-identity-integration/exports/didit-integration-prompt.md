# Integrate Didit into my application

You are integrating Didit (KYC, KYB, AML, biometrics) end-to-end. **Ground truth:** `.grok/skills/didit-identity-integration/references/didit-api-canonical.md` — if not listed there, fetch docs.didit.me; never invent API fields.

## My application context

<my_stack>
Stack: [from manifest — e.g. Laravel 12 + Filament 5 + Livewire]
App: [ndestates-io | e-ndsign | other]
Use case: [KYC at signer onboarding | KYB business onboarding | age gate | re-auth | other]
Database: [MySQL via DDEV]
</my_stack>

## Step 1 — Account + API key

Programmatic register + verify-email on `https://apx.didit.me` (see canonical ref). Persist `DIDIT_API_KEY`. Run guardian + security-audit before storing secrets.

## Step 2 — Pick approach (exactly one)

- **A Sessions + SDK** (default for end-user verification)
- **B Standalone APIs** (batch/back-office only)

## Step 3 — Workflow

Create or reuse workflow via `POST /v3/workflows/`. Save `DIDIT_WORKFLOW_ID`. No unknown body fields.

## Step 4 — SDK install

Match stack table in canonical ref (`@didit-protocol/sdk-web` for Laravel+Livewire public flows).

## Step 5 — Session + present UI

Backend `POST /v3/session/` with `vendor_data` = internal signer/user id. Frontend: SDK modal, iframe, or redirect to `url`.

## Step 6 — Webhook

`POST /api/webhooks/didit` — register destination once; verify `X-Signature-V2`; dedupe `event_id`; return 2xx within 5s.

## Step 7 — Apply decision

Map status strings case-sensitively to DB (e.g. Signer verified flag, request gate). Re-fetch decision via `GET /v3/session/{id}/decision/` if signature doubt.

## Verify before done

Sandbox session completes; webhook received and verified; guardian drift check passes; `/eval-maintenance-task --task=didit-identity`.