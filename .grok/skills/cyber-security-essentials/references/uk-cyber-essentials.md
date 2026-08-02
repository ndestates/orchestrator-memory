# UK Cyber Essentials — developer & code mapping

**Source:** [NCSC Cyber Essentials overview](https://www.ncsc.gov.uk/cyberessentials/overview) (five technical controls, v3.x via IASME).

This reference maps each control to **what engineers can verify in code, config-as-code, CI, and application design**. Full certification also requires organisational and infrastructure evidence (board sign-off, asset inventory, endpoint AV, boundary firewalls) — flag those as **out-of-code** when reporting.

## The five controls

| # | NCSC control | In-scope for this skill | Out-of-code (note in report) |
|---|--------------|-------------------------|------------------------------|
| 1 | **Firewalls** | App/network boundaries in code: bind addresses, ingress rules in IaC, API gateway, CORS, rate limits, WAF config in repo | Perimeter firewall rules, router config, cloud console-only rules |
| 2 | **Secure configuration** | Secure defaults, debug off in prod, security headers, TLS settings, secrets not in repo, minimal exposed surface, hardened Docker/compose | OS hardening, BIOS, physical devices |
| 3 | **User access control** | AuthN/AuthZ, RBAC/policies, least privilege, MFA enforcement, session timeout, admin separation, service account scopes | HR offboarding process, physical access |
| 4 | **Malware protection** | Dependency/supply-chain checks, file-upload validation, CI malware/secret scanning, signed commits policy | Endpoint AV on laptops/servers |
| 5 | **Security update management** | Pinned deps with update process, `composer audit` / `npm audit` / Dependabot, CVE response in CI, EOL runtime detection | Patch cadence for OS/firmware |

## Code & config checklist by control

### 1. Firewalls (application layer)

- [ ] Services bind to required interfaces only (not `0.0.0.0` in dev-only docs copied to prod)
- [ ] CORS allowlist is explicit (no `*` with credentials)
- [ ] Admin/internal routes not exposed on public ingress without auth
- [ ] Rate limiting on auth, signup, password reset, webhooks
- [ ] Webhook endpoints verify origin/signature
- [ ] IaC (Terraform, K8s manifests, DO App spec) restricts ingress to needed ports

### 2. Secure configuration

- [ ] `APP_DEBUG=false`, `APP_ENV=production` enforced in prod deploy config
- [ ] Security headers: HSTS, CSP (where feasible), X-Frame-Options, X-Content-Type-Options
- [ ] No default credentials in code or sample `.env` committed
- [ ] Secrets via env/secret manager — grep for API keys, passwords, private keys in repo
- [ ] Unnecessary endpoints disabled (telescope, horizon, phpinfo, debug routes)
- [ ] Error responses do not leak stack traces or SQL to users in prod
- [ ] Database and Redis not publicly reachable (connection strings, docker-compose)

### 3. User access control

- [ ] Authentication required for all non-public routes (policies, middleware, Filament `canAccessPanel`)
- [ ] Authorisation checks at action level (not UI-only hiding)
- [ ] Role/permission model documented; default-deny for sensitive operations
- [ ] MFA available/enforced for admin and privileged roles (where product supports)
- [ ] Session lifetime, secure cookie flags (`httpOnly`, `secure`, `sameSite`)
- [ ] Password policy and throttling on login/trial/signup flows
- [ ] Service accounts / API tokens scoped minimally; rotation documented
- [ ] No shared admin accounts in config

### 4. Malware protection (supply chain & uploads)

- [ ] Lockfiles committed (`composer.lock`, `package-lock.json`, `pnpm-lock.yaml`)
- [ ] CI runs dependency audit (composer/npm/pip) and secret scanning (GitGuardian, etc.)
- [ ] File uploads: type/size limits, storage outside webroot, no executable extensions
- [ ] Third-party scripts/CDN integrity (SRI) where used
- [ ] No unsigned or unreviewed binary blobs in repo

### 5. Security update management

- [ ] Dependabot or equivalent enabled for the repo
- [ ] CI fails or warns on known critical CVEs in direct dependencies
- [ ] Runtime versions documented (PHP, Node, Python) and not EOL
- [ ] Container base images pinned and periodically rebuilt
- [ ] Changelog/process for applying security patches within agreed SLA

## UK context beyond Cyber Essentials (code-relevant)

| Topic | Practice |
|-------|----------|
| **UK GDPR / DPA 2018** | Data minimisation in forms/APIs; lawful basis documented; retention; encryption in transit (TLS) and at rest where appropriate; subject-access/delete hooks |
| **NCSC developers' collection** | Follow [NCSC developer guidance](https://www.ncsc.gov.uk/collection/developers) for input validation, output encoding, auth patterns |
| **Logging & monitoring** | Security events logged without PII leakage; no secrets in logs |

## Severity mapping (for reports)

| Rating | Meaning |
|--------|---------|
| **CE-critical** | Fails a Cyber Essentials control in a way likely to fail certification (e.g. secrets in git, no auth on admin) |
| **CE-high** | Significant gap; remediate before certification or supplier assurance |
| **CE-medium** | Partial compliance; document compensating controls |
| **CE-low** | Hardening; good practice |
| **CE-info** | Organisational evidence needed; code OK |

## References

- [NCSC Cyber Essentials](https://www.ncsc.gov.uk/cyberessentials/overview)
- [Requirements for IT Infrastructure (IASME/NCSC PDF)](https://www.ncsc.gov.uk/sites/default/files/documents/cyber-essentials-requirements-for-it-infrastructure-v3-3.pdf)
- [NCSC Collection: Developers](https://www.ncsc.gov.uk/collection/developers)