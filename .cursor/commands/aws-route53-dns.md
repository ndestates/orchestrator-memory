# /aws-route53-dns

> AWS Route 53 expert: hosted zones, production app DNS (A/CNAME/ALIAS), deploy-time DKIM/SPF/DMARC/MX for SES, nameserver delegation, DNS-as-code change batches.

**Platform:** Cursor · same skill as Grok `/aws-route53-dns` · Claude `/aws-route53-dns`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `Task (e.g. "deploy app CNAME to DO", "full SES DKIM SPF DMARC batch", "pre-go-live DNS + firewall checklist", "delegate NS to Route53")`

# AWS Route 53 DNS Setup for project Domains (Domains + Email Records + Verification)

**Goal:** Authoritative, reliable DNS via AWS Route 53 for the target application domain (from user, manifest, or cache). Focus on email deliverability and authentication for Amazon SES (transactional send + inbound mail as required by the app). This skill provides the DNS half of SES setup — programmatic record management instead of manual edits in DO DNS or registrar. Non-Microsoft (AWS Route53 + SES only). Supports domain apex + subdomains, nameserver delegation, and verification.

**Core mandate:** DNS is critical infrastructure (Stage 6 agent slot). Cache-backed (current zone/records from prior scans), drift-gated (every change via /project-drift-guardian — DNS mismatches cause email blackholing or spoofing failures), security-first (IAM least-privilege, no broad zone access), observable (dig checks + propagation), repeatable via AWS CLI one-liners + JSON change batches. Never manual edits. Treat record sets as code. Use host for `aws route53`; cross with DDEV only for app-side verification.

This skill is self-contained, references project skills (load-project-cache-first, cache-efficient, project-drift-guardian, amazon-ses-email, digitalocean-app-platform-docr-deploy, git-workflow-guardrails, security-audit-agent, eval/maintenance-task), and provides precise `aws route53` commands, change-batch examples for SES email records, delegation steps, verification, and integration points.

## Mandatory Start (cache + context — per all project skills)
1. `/load-project-cache-first` (or /cache-efficient) — load INDEX, docs/codebase/ (INTEGRATIONS for current DNS state, ARCHITECTURE/STACK for email flows, CONCERNS for DNS drift risks), TODO-2026-06-14.md, prior evals.
2. `/project-drift-guardian` (or drift-check) — run with scope including "DNS" or "Route53 email records" or "domain delegation". Non-negotiable: DNS changes are high-risk for drift (propagation, NS delegation, record mismatches with SES).
3. Cross-load: amazon-ses-email (SES tokens before DKIM UPSERT), `/github-expert` + `/github-workflow-expert` (CI DNS validation jobs), `/git-workflow-guardrails` (commit `infra/dns/*.json`), `/docker-expert` + `/digitalocean-app-platform-docr-deploy` (app hostname targets + **Cloud Firewall** — Route 53 does not enforce packet filters), security-audit-agent (IAM), project-drift-guardian.
4. Confirm current state: git status, current domain(s), existing hosted zone ID (if any), last known SES verification status, registrar (DO or other), AWS region (prefer us-east-1).

Never proceed without these. After changes: update docs/codebase/INTEGRATIONS.md, CONCERNS if new risks, drift requirements DB, and run /eval-maintenance-task.

**Non-Microsoft policy:** Pure AWS (Route 53 for all DNS + SES for email). No Microsoft DNS, Azure DNS, Office 365 DNS, or third-party like Cloudflare if it conflicts with "non-MS AWS" direction. Use Route 53 exclusively for project domains.

## Route 53 Overview for project + Email
- **Hosted Zone:** Public hosted zone for the domain (or subdomain). Route 53 becomes the authoritative nameserver.
- **Nameserver Delegation:** Get the 4 NS records from the zone and set them at the domain registrar (or DO nameservers panel if currently using DO DNS).
- **Email Records (tied to /amazon-ses-email):**
  - Domain verification TXT (from `aws ses verify-domain-identity`).
  - DKIM: 3 CNAME records (from `aws ses verify-domain-dkim`).
  - SPF: TXT at apex (or include in existing SPF).
  - DMARC: TXT at _dmarc.
  - MX: for inbound receiving (points to SES inbound-smtp).
- **Other common:** A/AAAA or CNAME for app (e.g. app.project.com), CAA for security, custom MAIL FROM subdomain if used.
- **Verification:** After upsert, poll SES `get-identity-verification-attributes`, use `dig` +short to confirm propagation (can take minutes to hours for NS change).
- **Drift risks:** NS delegation at registrar, record values from SES tokens, TTLs, apex vs www handling. Guardian + record exports as code mitigate.
- **Costs:** Route 53 hosted zones + queries (low for project transactional use). Monitor in AWS billing.

**References (load first):** docs/codebase/INTEGRATIONS.md (DNS/Email section), CONCERNS.md (SES DNS drift + new Route53 section), .grok/prompts/aws-route53-dns-setup.md (this prompt), amazon-ses-email skill (for token generation + Laravel side), digitalocean skill (registrar/NS steps), project-drift-guardian (DNS checks).

## Setup Procedures (one-liners + change batches + verification)
Always: Authenticate with limited AWS creds (`aws configure` or env). Prefer us-east-1. Run on host (not inside DDEV containers for AWS CLI). After SES commands produce tokens, immediately apply via this skill.

### 1. Create or Identify Hosted Zone
```bash
# List existing (note the Id, e.g. /hostedzone/Z0123456789ABC)
aws route53 list-hosted-zones --region us-east-1

# Create new public zone (caller-reference must be unique)
aws route53 create-hosted-zone \
  --name project.com \
  --caller-reference "$(date +%s)-project" \
  --region us-east-1
# Capture the Id (Z...) and the 4 NameServers from output.DelegationSet.NameServers
```

Store the HostedZoneId (e.g. ZXXXXXXXXXXXXX) for all future commands. Update cache/docs with it.

### 2. Delegate Nameservers (Critical for live domain)
- From the create output (or `aws route53 get-hosted-zone --id Z...`), copy the 4 NS values.
- At your registrar (DO Domains, or wherever project.com is registered):
  - Change nameservers from current (DO or registrar defaults) to the four Route53 NS values.
  - Remove any old DNS records at the old provider after delegation succeeds (to avoid split-brain).
- Propagation for NS change can take 24-48h (usually faster). Monitor with:
```bash
dig NS project.com +short
dig +trace project.com   # to confirm authority
```

Use /digitalocean-app-platform-docr-deploy for DO-specific registrar instructions if applicable. Always run guardian before registrar changes.

### 3. Apply SES Email DNS Records (Verification, DKIM, SPF, DMARC, MX)
**Prerequisite:** Run the SES verification first (see /amazon-ses-email):
```bash
aws ses verify-domain-identity --domain project.com --region us-east-1
aws ses verify-domain-dkim --domain project.com --region us-east-1
# Note: VerificationToken and the three DkimTokens
```

Create a change batch JSON (store in repo under e.g. infra/dns/ or .grok/ for reference — treat as code):

Example `changes-ses-email.json` (adapt tokens):
```json
{
  "Comment": "project SES email setup (verification + DKIM + SPF + DMARC + MX) - $(date)",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "_amazonses.project.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"<VerificationToken-from-SES>\""}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "selector1._domainkey.project.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "<token1>.dkim.amazonses.com"}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "selector2._domainkey.project.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "<token2>.dkim.amazonses.com"}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "selector3._domainkey.project.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "<token3>.dkim.amazonses.com"}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "project.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"v=spf1 include:amazonses.com ~all\""}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "_dmarc.project.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"v=DMARC1; p=quarantine; rua=mailto:dmarc@project.com\""}]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "project.com",
        "Type": "MX",
        "TTL": 300,
        "ResourceRecords": [{"Value": "10 inbound-smtp.us-east-1.amazonaws.com"}]
      }
    }
  ]
}
```

Apply it:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0123456789ABC \
  --change-batch file://changes-ses-email.json \
  --region us-east-1
```

**Note on SPF:** If an apex TXT SPF already exists (from prior provider), merge the include:amazonses.com value instead of creating a second TXT at root (Route53 allows only one TXT per name for SPF best practice).

### 4. Verify Records + SES Status
```bash
# Local verification (after short propagation)
dig TXT _amazonses.project.com +short
dig CNAME selector1._domainkey.project.com +short
dig TXT _dmarc.project.com +short
dig MX project.com +short

# SES side
aws ses get-identity-verification-attributes --identities project.com --region us-east-1
aws ses get-identity-dkim-attributes --identities project.com --region us-east-1
```

Once SES shows "Success" for verification and DKIM, proceed to Laravel config and testing (see /amazon-ses-email).

### 5. IAM Least-Privilege for Route53 (DNS only)
```bash
aws iam create-user --user-name project-route53
aws iam create-access-key --user-name project-route53

# Minimal policy (attach via put-user-policy or console). Scope to specific zone when possible.
aws iam put-user-policy --user-name project-route53 --policy-name Route53DnsManage --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:ListHostedZones",
        "route53:GetHostedZone",
        "route53:ListResourceRecordSets",
        "route53:ChangeResourceRecordSets"
      ],
      "Resource": "arn:aws:route53:::hostedzone/Z0123456789ABC"
    }
  ]
}'
```

Store keys in DO secrets (never commit). Prefer IAM roles for EC2/App Platform where possible. Run security-audit-agent after.

### 6. Production deploy DNS package (app + email + perimeter)

**Chain:** `/chain deploy-dns-infra` — Route 53 records → DO firewall → SES verify → git commit DNS JSON.

Route 53 owns **names and records**; **firewalls** are provisioned on the compute platform (delegate to DO skill):

| Layer | Owner skill | What to configure |
|-------|-------------|---------------------|
| DNS (app) | This skill | `app.` CNAME → DO App Platform default ingress; `api.` if split; ACM validation CNAMEs |
| DNS (email) | This skill + `/amazon-ses-email` | Verification TXT, **3× DKIM CNAME**, SPF TXT, DMARC `_dmarc`, MX inbound |
| Firewall | `/digitalocean-app-platform-docr-deploy` | DO Cloud Firewall: **inbound 80/443** (world or CDN), **SSH 22** from allowlist only, **deny DB/Redis ports** from internet |
| TLS | DO App Platform or droplet | Auto TLS after DNS points correctly |

#### Pre-go-live DKIM / email checklist (all must PASS)

| # | Check | Command / action |
|---|-------|------------------|
| 1 | SES domain verified | `aws ses get-identity-verification-attributes` → Success |
| 2 | DKIM enabled + 3 CNAMEs in zone | `aws ses get-identity-dkim-attributes` + `dig CNAME selector1._domainkey` |
| 3 | SPF includes `amazonses.com` | `dig TXT apex +short` — single merged TXT |
| 4 | DMARC published | `dig TXT _dmarc +short` |
| 5 | MX for inbound (if receive) | `dig MX +short` → `inbound-smtp.*.amazonaws.com` |
| 6 | MAIL FROM subdomain (if used) | MX + SPF on bounce subdomain |
| 7 | DNS JSON in repo | `infra/dns/<domain>-ses.json` committed via `/git-workflow-guardrails` |
| 8 | Firewall blocks DB port | `doctl compute firewall list` / rules audit per DO skill |

#### App deploy records (example UPSERT)

```json
{
  "Action": "UPSERT",
  "ResourceRecordSet": {
    "Name": "app.project.com",
    "Type": "CNAME",
    "TTL": 300,
    "ResourceRecords": [{"Value": "<app-platform-default-domain>.ondigitalocean.app"}]
  }
}
```

Store batches under `infra/dns/`; never commit AWS keys. After UPSERT: `dig app.project.com +short`, hit HTTPS, then `/eval/maintenance-task`.

#### Firewall handoff to DigitalOcean

Document required rules in handoff `firewall_spec`:

- Ingress: TCP 443 (and 80 redirect) from `0.0.0.0/0` or CDN edge only
- Ingress: TCP 22 from operator IP / bastion CIDR only
- Deny: 3306, 5432, 6379, 27017 from `0.0.0.0/0`
- Egress: allow HTTPS for package/registry pulls as needed

Invoke `/digitalocean-app-platform-docr-deploy` with `firewall_spec` — do not open DB ports in Route 53 (DNS cannot fix bad firewall posture).

### 7. Additional / Ongoing Records + Cleanup
- App subdomains, www redirect CNAMEs, etc.: similar UPSERT batches.
- Custom MAIL FROM (if used): additional MX + TXT for feedback.
- Cleanup old records (Action: DELETE) after successful delegation + verification.
- Export current zone for "as code" reference:
```bash
aws route53 list-resource-record-sets --hosted-zone-id Z... --region us-east-1 > infra/dns/project.com-current.json
```

### 8. Monitoring, Drift & Production
- After any change: `/project-drift-guardian --scope "Route53 DNS + SES email records"` + `/eval-maintenance-task --task=route53-dns`.
- Update INTEGRATIONS.md with zone ID, record summary, NS values (sanitized).
- In CI/digitalocean flows: optional dry-run or validation step using the exported JSON.
- Propagation + email tests: send test, check DMARC reports, inbound to support@.

**One-liner full flow (cache-verified, after SES tokens obtained):**
```bash
# 1. Ensure zone + delegation (one-time)
aws route53 create-hosted-zone --name project.com ...
# Set NS at registrar (manual or via registrar API)

# 2. Apply email records (idempotent UPSERT)
aws route53 change-resource-record-sets --hosted-zone-id Z... --change-batch file://changes-ses-email.json

# 3. Verify
dig ... && aws ses get-identity-verification-attributes ...
ddev exec php artisan config:clear   # once Laravel side updated
# Then full SES tests + guardian + eval
```

**Security & Governance (Stage 4 — mandatory):**
- IAM scoped to the exact hosted zone ARN (never *).
- Change batches reviewed (store JSON in repo).
- Registrar NS delegation is a high-privilege external change — double-check, use guardian, document.
- No PII or secrets in DNS records (DMARC rua is fine; avoid exposing internal hosts).
- Full checklist on new prompts/scripts or IAM changes.
- Cost + query logging via CloudWatch/Route53 resolver if expanded.

**Cross-references (max cache):**
- /load-project-cache-first + /project-drift-guardian (mandatory for every DNS op) + /amazon-ses-email (token source + Laravel + receiving).
- /digitalocean-app-platform-docr-deploy (registrar/NS delegation + DO secrets for Route53 keys).
- /security-audit-agent (IAM + delegation).
- /eval/maintenance-task (post DNS + email verification).
- docs/codebase/ (email + DNS in integrations/concerns).
- .grok/prompts/aws-route53-dns-setup.md
- copilot-instructions (DDEV local, branch rules, security on external changes).

**Advancement (AI Engineering Maturity):** Makes DNS a first-class, invocable, cache-backed, guardrailed part of the platform (Stage 6). Eliminates ad-hoc registrar edits. Future: scripted delegation (if registrar API), zone versioning in repo, automated drift detection on record sets vs expected JSON, or Route53 profiles.

Invoke for any DNS task: `/aws-route53-dns "apply full SES verification + DKIM + MX records for project.com using Route53"`. After: update TODO + cache + drift DB. Re-run security checklist.

This completes reliable AWS-native (non-MS) domain + email DNS for project when combined with /amazon-ses-email. Cite https://upsun.com/blog/8-stages-ai-engineering-maturity/ when using.

(Adapted from patterns in amazon-ses-email, project-drift-guardian, digitalocean skills; made specific to project email flows + Route 53 automation.)

User focus (optional): use any extra chat text as $ARGUMENTS.
