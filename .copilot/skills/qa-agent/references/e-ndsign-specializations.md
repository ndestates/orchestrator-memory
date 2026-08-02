# e-ndsign Specializations

**Project-specific QA checklist items** for the e-ndsign wave project (Laravel e-signature platform).

Focus: signing flows, identity, address, billing, document integrity, compliance.

## E-Sign Domain & Integrations

- Didit identity verification (KYC/KYB/AML, biometrics, sessions) flows correct: session creation, status polling, webhook/HMAC validation, result storage.
- Loqate (GBG) address capture: Find + Retrieve type-ahead, normalized storage, validation on signer/billing addresses.
- PayPal billing: checkout flows, invoice/receipt generation, webhook handling for payments/disputes, refunds tied to e-sign usage.
- Document / canvas / PDF handling: embed, audit, signature placement, canvas data integrity, no tampering.
- Signing workflows: multi-signer, order, reminders, completion events, audit trail completeness.
- Consent / data protection: explicit consent capture, retention, deletion paths.
- Specific scripts/areas: signature capture, PDF generation, verification callbacks.

## Safety & Compliance

- All sensitive ops (identity, payments, documents) run with proper test data isolation.
- Secrets (API keys for didit, loqate, paypal) never leak in code, logs, reports, or diffs.
- Webhook verification (HMAC, signatures) implemented and tested.
- Test DB only; never hit live Didit/Loqate/PayPal without explicit approval + mocks where possible.

## Testing & Verification

- `test-safety-agent` before tests.
- Targeted tests for didit integration, loqate address, paypal billing, signing flows, PDF rendering.
- End-to-end signing simulation (with mocks for external services).
- Regression on high-churn areas: signing UI, document processing, integration callbacks.

## Project Process

- Branch alignment with e-ndsign feature work.
- Cache + TODO updates for signing/compliance features.
- Full audit trail for any change affecting signatures or personal data.
