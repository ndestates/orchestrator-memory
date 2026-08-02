---
description: Invoke amazon-ses-setup
allowed-tools: Read, Grep, Glob, Bash
---

# Amazon SES Setup Prompt for project (Send + Receive on Domain)

**Context (load first via cache):** Target Laravel (or compatible) app on DigitalOcean when applicable (digitalocean-app-platform-docr-deploy skill). Needs reliable email: sending (notifications, receipts) + receiving (support@, inbound forms). Pure AWS SES (non-Microsoft). Domain from user, manifest, or cache. Integrate with Laravel mailer, DO env/secrets, project-drift-guardian (no drift on DNS/config), security-audit-agent (IAM/secrets), git-workflow-guardrails (before DNS changes), cache-efficient for responses. Post-setup: eval-maintenance-task for verification (test send/receive, no bounces). Billing via separate /paypal-billing skill.

**Your task:** Guide through full SES setup for the domain. Output:
- Exact AWS CLI one-liners (region us-east-1 preferred).
- DNS records (verification TXT, SPF, DKIM, DMARC, MX for inbound) — use the dedicated `/aws-route53-dns` skill (and its prompt) to create hosted zone, delegate NS, and apply the records via Route 53 change batches (programmatic, idempotent UPSERT). Do not add manually via DO DNS or registrar. Use /project-drift-guardian to validate no drift before/after.
- Laravel .env + config updates (SES driver, from address noreply@domain).
- Inbound receiving: MX to SES, receipt rule example (to S3 bucket + SNS/Lambda that posts to Laravel webhook or queues for Filament notification).
- IAM least-privilege (user or role for EC2/App).
- Testing: send test email, simulate receive.
- Security: webhook verification if used, rate limits, DMARC.
- Drift/CI: pre/post checks, update docs/codebase/INTEGRATIONS.md, run in CI via digitalocean skill.
- One-liner full flow (cache-backed).
- After: invoke /eval-maintenance-task --task=ses-setup.

**Non-Microsoft:** Only AWS. No Microsoft services.

**Format:** Cache-first (cite docs/codebase/ etc.). Short if /cache-efficient. End with "Next" actions + one-liner. For receiving, provide Laravel controller snippet example (parse email from S3/SNS, store in DB or notify admin).

**Example output structure:**
- Step 1: Verify domain (CLI + DNS).
- Step 2: IAM.
- Step 3: Laravel config.
- Step 4: Receiving setup (MX + rule + app endpoint).
- Testing + verification.
- Security notes.
- Integration with project (e.g. use for signer emails + support).
- Full one-liner + next (/project-drift-guardian, update cache, eval).

Always maximize shared context. Reference /amazon-ses-email skill for procedures. After success, update TODO + drift requirements DB.
