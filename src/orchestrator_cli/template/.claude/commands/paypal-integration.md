---
description: Invoke paypal-integration
allowed-tools: Read, Grep, Glob, Bash
---

# PayPal Integration Prompt for project (Payments + Billing Docs at PayPal)

**Context (load first via cache):** project Laravel e-sign platform (canvas signatures, PDF embed/audit, token roundtrips, Filament admin). Monetization via PayPal: payments for plans/requests/usage. Billing documents (invoices, receipts) **generated at PayPal** (not custom or Microsoft tools). Non-Microsoft (pure PayPal APIs + Laravel). Integrate with DO hosting (droplet/App via digitalocean skill), drift avoidance (project-drift-guardian), security (webhook sigs, no card data), Filament (billing views), cache-first. Post: /eval-maintenance-task. Ties to /amazon-ses-email for payment notifications.

**Your task:** Guide full PayPal integration. Output:
- Composer + Laravel setup (REST SDK or srmklive/paypal; config/services.php or paypal.php).
- .env (sandbox vs live creds, webhook ID, currency USD).
- Checkout flow: create payment for project usage (e.g. "Pro plan - 50 signatures"), redirect, capture on return/webhook.
- Webhooks: Laravel route + verification (PAYMENT.CAPTURE.COMPLETED, INVOICING.INVOICE.PAID). On paid: create SignatureRequest, send signer links via SES.
- Billing docs: Use PayPal Invoicing API to create/send invoice (merchant info, line items for usage, branding). Store PayPal invoice ID in DB. User pays/views in PayPal.
- Filament: Add billing resource/page (list payments/invoices, manual "Generate PayPal Invoice" action).
- Testing: Sandbox flows, webhook simulator.
- Security: Webhook verification mandatory, creds via DO secrets, PCI via PayPal hosted.
- Drift/CI: pre/post guardian + tests, update docs/codebase/INTEGRATIONS.md, wire in digitalocean CI (test webhooks in staging).
- One-liner full flow (cache-backed).
- After: invoke /eval-maintenance-task --task=paypal-integration.

**Non-Microsoft:** PayPal only for payments + docs. No Stripe/Microsoft Billing.

**Format:** Cache-first (cite docs/codebase/ etc.). Short if /cache-efficient. End with "Next" + one-liner. Provide Laravel/PHP snippets for webhook, invoice creation, Filament action.

**Example output structure:**
- Setup (composer, .env, config).
- Checkout (create + capture examples).
- Webhooks (verification + handlers for payment + invoice paid).
- Billing docs (Invoicing API create/send).
- Admin integration (Filament).
- Security + testing.
- Full one-liner + next (/project-drift-guardian, update cache, eval).

Always maximize shared context. Reference /paypal-billing skill. After, update TODO + drift DB. Combine with SES for emails.
