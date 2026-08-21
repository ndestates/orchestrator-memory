# AWS Route 53 DNS Prompt for project (Domains, Email Records, DKIM, SPF, Verification)

**Context (load first via cache):** Target application requiring DNS (often Laravel on DigitalOcean). Primary email via Amazon SES (see /amazon-ses-email skill). AWS Route 53 as authoritative DNS for the domain to manage verification, DKIM, SPF, DMARC, MX and other records programmatically. Pure AWS (non-Microsoft). Domain from user, manifest, or cache. 

Integrate with: /load-project-cache-first (or cache-efficient), /project-drift-guardian (DNS changes are extremely drift-prone — NS delegation, record values, propagation), /amazon-ses-email (run SES verify-domain-identity + verify-domain-dkim FIRST to obtain tokens, then apply via Route53), /digitalocean-app-platform-docr-deploy (registrar delegation if domain at DO, secrets for Route53 IAM keys, current DNS state), security-audit-agent (IAM scoping + delegation), git-workflow-guardrails (before committing change-batch JSONs), eval-maintenance-task (post DNS + email tests). Post-setup: update docs/codebase/INTEGRATIONS.md and CONCERNS.md.

**Your task:** Guide the user through complete Route 53 DNS setup focused on domains + email (mails, DKIM, SPF, verification). 

Output must include:
- Exact `aws route53` one-liners and JSON change-batch examples (hosted zone create/list, change-resource-record-sets with UPSERT for verification TXT, 3x DKIM CNAMEs, SPF TXT, DMARC TXT, MX).
- Nameserver delegation steps (extract 4 NS from zone, set at registrar/DO, verification with dig +trace).
- Prerequisite flow: run relevant SES commands first (verify + dkim), capture tokens, then build/apply the Route53 batch (reference /amazon-ses-email).
- IAM least-privilege user/policy scoped to the specific hosted zone.
- Verification commands: dig for all records + `aws ses get-identity-*` + propagation notes.
- How to store change batches or current zone export as code (for drift comparison).
- Drift/CI/guardian: always call /project-drift-guardian with DNS scope before and after; treat records as code.
- One-liner full flow (cache-backed).
- Laravel/DO side notes only at high level (actual config in the SES skill).
- After success: invoke /eval-maintenance-task --task=route53-dns + update cache/TODO/INTEGRATIONS.
- Security notes (scoped IAM, registrar change risks, no secrets in records).

**Non-Microsoft:** Only AWS Route 53 (and SES). No Microsoft DNS services, Azure DNS, or mixed providers that introduce drift.

**Format:** Cache-first (cite docs/codebase/INTEGRATIONS.md, CONCERNS.md, the skills, etc.). Short bullets if /cache-efficient. End with "Next" actions + ready-to-run one-liner. Provide copy-pasteable JSON examples (with placeholders for tokens/zone ID). Warn about NS propagation time and idempotency (UPSERT).

**Example output structure:**
- Step 0 (mandatory): Load cache + run /project-drift-guardian --scope "Route53 DNS email records".
- Step 1: Create or locate hosted zone (list + create commands + capture Z-ID and NS).
- Step 2: Delegate nameservers at registrar (exact steps + dig verification commands).
- Step 3: SES prerequisites (verify-domain-identity + verify-domain-dkim) — link to /amazon-ses-email.
- Step 4: Build & apply email DNS records (full example changes-*.json for _amazonses TXT, DKIM CNAMEs x3, SPF, DMARC, MX + the route53 change command).
- Step 5: Verification (dig for each record type + SES get-identity commands).
- Step 6: IAM setup (create user + minimal policy example scoped to the zone ARN).
- Step 7: Additional records, exports for "as code", cleanup.
- Testing + monitoring.
- Security + drift notes.
- Full one-liner + next steps (/project-drift-guardian, /eval-maintenance-task, update docs, test SES send/receive end-to-end).

Always maximize shared context. Reference the full procedures in `.grok/skills/aws-route53-dns/SKILL.md`. After any successful DNS application, update TODO + drift requirements DB + INTEGRATIONS.md. Combine tightly with the SES skill (this is the DNS execution half).

**Important:** Emphasize idempotency via UPSERT, storing the change batch JSON in the repo (infra/dns/ or similar), and running guardian on the batch before applying. For NS delegation, stress the external registrar step and risk of downtime during cutover.
