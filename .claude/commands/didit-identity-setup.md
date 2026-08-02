---
description: Invoke didit-identity-setup
allowed-tools: Read, Grep, Glob, Bash
---

# Didit Identity Setup Prompt for project (KYC / KYB / AML)

**Context (load first via cache):** Laravel app (`e-ndsign` signer verification or `ndestates-io` optional KYB). Didit Sessions + SDK default. Canonical API: `.claude/commands/didit-identity-integration/references/didit-api-canonical.md`. Export: `exports/didit-integration-prompt.md`. Integrated with drift-guardian, security-audit, laravel-expert, eval.

**Your task:** Guide full Didit integration per canonical ref only — never invent API fields. Output:
- Account + `DIDIT_API_KEY` (programmatic register/verify).
- Workflow create → `DIDIT_WORKFLOW_ID`.
- Session create + SDK/iframe presentation.
- Webhook `POST /api/webhooks/didit` with `X-Signature-V2` verification + `event_id` dedupe.
- DB mapping for Signer/customer verification status (case-sensitive status strings).
- Env vars via DDEV/DO secrets; sandbox-first.
- Drift/CI: guardian pre/post; update `docs/codebase/INTEGRATIONS.md`.
- After: `/eval-maintenance-task --task=didit-identity`.

**Format:** Cache-first. Short if `/cache-efficient`. End with Next + verification checklist.

**Skill:** `.claude/commands/didit-identity-integration/SKILL.md`
