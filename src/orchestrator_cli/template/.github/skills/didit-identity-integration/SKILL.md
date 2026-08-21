---
name: didit-identity-integration
description: "Full skill for Didit identity verification (KYC, KYB, AML, biometrics) in Laravel app repos."
argument-hint: 'Task (e.g. "setup Didit KYC session for signers", "register Didit webhook with V2 signature", "create KYC workflow via API")'
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
verified_at: "2026-08-16"
self_regulating: true
covers:
  - .github/skills/didit-identity-integration
  - .github/skills/didit-identity-integration/references/didit-api-canonical.md
---
# Didit Identity Integration (KYC / KYB / AML)

**Goal:** End-to-end Didit verification in Laravel apps. Pay-per-call identity infra behind one API. Non-Microsoft; complements Loqate (address) and PayPal (billing) — does not replace them.

**Canonical facts (mandatory):** Grep then section-read `.github/skills/didit-identity-integration/references/didit-api-canonical.md` before any API work. **Never invent** endpoints, fields, or status strings. Copy-paste agent entry: `exports/didit-integration-prompt.md`.

## Mandatory Start
1. `.github/prompts/load-project-cache-first.prompt.md` — INTEGRATIONS.md, CONCERNS.md (PII/compliance), ARCHITECTURE (signer flows).
2. `.github/skills/project-drift-guardian/SKILL.md` — scope webhook routes, env vars, workflow IDs.
3. Cross-load: `security-audit-agent`, `laravel-expert-agent`, `git-workflow-guardrails`, `eval/maintenance-task`.
4. Confirm: sandbox vs live, `DIDIT_API_KEY` present, webhook URL matches public app URL (DO).

**Current wiring:** skills only — no Didit package/routes until invoked in the app.

## Procedures (summary — details in canonical ref)

1. **Account:** programmatic register + verify-email → `DIDIT_API_KEY`.
2. **Workflow:** `POST /v3/workflows/` — save `DIDIT_WORKFLOW_ID`.
3. **Approach A (default):** `POST /v3/session/` → SDK/iframe → webhook `status.updated`.
4. **Webhook:** `POST /api/webhooks/didit` — `X-Signature-V2`, replay window 300s, idempotent `event_id`.
5. **Apply decision:** map case-sensitive status to DB; optional `GET /v3/session/{id}/decision/` for fresh presigned media.

## Laravel touchpoints

- `Signer` model: `verification_status`, `didit_session_id`, `verified_at`.
- Routes: webhook (no CSRF), optional admin Filament status column.
- Env via DO secrets: `DIDIT_API_KEY`, `DIDIT_WORKFLOW_ID`, `DIDIT_WEBHOOK_SECRET`.

## Security (non-negotiable)

- Webhook signature verification before trusting `decision`.
- `session_token` and `api_key` are secrets — never log or expose to browser.
- Check `environment` (`sandbox`|`live`) before mutating production signers.
- PII in decision payloads — retention policy + CONCERNS update.

## Post-setup

`/eval/maintenance-task --task=didit-identity` · update `docs/codebase/INTEGRATIONS.md` · guardian re-check.

Invoke: `/didit-identity-integration "setup KYC webhook for signers"`.

## Self-regulation (mandatory)

Follow [self-regulating-loop.md](../../references/self-regulating-loop.md).

**This skill's checks:**
- Grepped the canonical API ref; did not invent endpoints or status strings
- No API keys or webhook secrets in notes

Then: `python3 scripts/skill_health.py log --skill didit-identity-integration --score 0.0-1.0 --notes "api"`