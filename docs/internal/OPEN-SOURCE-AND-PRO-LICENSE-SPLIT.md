> **SUPERSEDED 2026-08-01 for public product:** Freeware Apache-2.0 + optional Patreon only. Pro £99 keys are not the product model. See docs/reference/licensing.md.

# Open-source core + Pro commercial split

**Date:** 2026-07-22  
**Branch:** `feature/opensource-apache-patreon-2026-07-22`  
**Status:** **HELD READY** — §2 EULA outline + §3 keep-closed inventory drafted; **pause implementation** (Apache root swap / counsel / Patreon) until operator unholds. Draft for human / counsel review — **not** lawyer-final.  
**Related:** `FREEMIUM-PRODUCT-FREEZE.md`, `FREEMIUM-LICENSE-AND-SERVER-PLAN.md`, `RELEASE-EXCLUSION.md`, `docs/reference/licensing.md`

> Internal commercial + legal architecture. Do not publish this file on the public docs site or in npm/PyPI packages.

---

## 0. Decision (frozen for planning)

| Layer | Instrument | Audience |
|-------|------------|----------|
| **Public OSS core** | **Apache License 2.0** (planned root `LICENSE`) | Developers, Light users, contributors, Patreon community |
| **Paid Pro (non-developer / company)** | **Commercial EULA + Subscription Terms** (§2) | Paying companies (£99/mo or £990/yr) |
| **Closed surfaces** | **Not Apache’d** — stay private / out of public tree (§3) | ND Estates operators only |
| **Patreon** | Patronage / sponsorship (not a Pro license key unless productized later) | Supporters |

**Product plumbing unchanged:** one public package (option A); Light free selections; Pro unlocked by company license key against the license server. See freemium freeze.

**Risk note:** Apache-2.0 on published source means skilled parties can strip soft client gates. Pro revenue relies on keys + closed server + support/official packaging + trademark — not on re-licensing the same files as proprietary.

**Counsel:** ND Estates Limited (Jersey) should review §2 and public Apache adoption before merge to `master`.

---

## 1. What ships where (summary)

```
Public GitHub (Apache-2.0)          Pro commercial product
─────────────────────────          ──────────────────────
CLI + Light selections             Company license key
Public skills/chains/docs          Full selections (mcp, wiki, platforms…)
Install from npm/pip/git           Official Pro entitlement + support
Fail-open / Light without key      Validate via license-api (closed)
Patreon → maintenance funding      PayPal/portal purchase flow (closed)
```

| SKU | Price | Software rights | Entitlement |
|-----|-------|-----------------|-------------|
| **Light** | Free | Apache-2.0 on public code | `TRIAL_LITE` / Light selections |
| **Pro monthly** | £99 / company / month | Apache on public code **plus** Pro EULA for product use | `PRO_FULL` via key |
| **Pro annual** | £990 / year (10× monthly) | Same | Same |
| **First-party** | n/a | Internal ND Estates | Full via allowlist / remotes |

Pro customers still receive Apache rights on **published OSS files**. The EULA governs the **subscription, key, official product claims, and closed services** — it does not revoke Apache grants on already-public code.

---

## 2. Commercial EULA + Subscription Terms (Pro)

**Working titles (public-facing, when ready):**

1. **Orchestrator Pro — End User License Agreement (EULA)**  
2. **Orchestrator Pro — Subscription Terms**  

**Licensor:** ND Estates Limited (confirm registered details with counsel).  
**Product:** Orchestrator Pro (company subscription; one key per organization).  
**Not for:** Light-only / pure OSS clone use without a Pro key (those stay under Apache + freemium policy only).

### 2.1 EULA outline (placeholder — counsel to finalize)

| § | Topic | Draft intent |
|---|--------|--------------|
| 1 | Parties & acceptance | Company customer accepts by purchasing, activating a key, or using Pro with a key |
| 2 | Grant | Non-exclusive, non-transferable right to use **Orchestrator Pro** for the customer’s internal business during an active subscription |
| 3 | Scope | One **company** (organization) per key; seats may share the key (no seat metering in v1) |
| 4 | What is included | Full deploy selections while key valid; access to updates for the subscribed term; optional support if tier includes it |
| 5 | What is not included | Cloud AI provider subscriptions (Grok/Claude/etc.); Ollama/BYOM is customer-managed; no warranty of third-party APIs |
| 6 | License keys | Keys are confidential; no sharing outside the company; no resale/sublicense of keys |
| 7 | Restrictions | No reverse-engineering or attacking the **license validation service**; no removing validation from **official Pro distribution** you ship/support; no offering Orchestrator as a competing hosted product using ND Estates trademarks |
| 8 | Open-source notice | Public components remain available under Apache-2.0; EULA does not limit rights **to those published files** under Apache; EULA covers Pro product, keys, and closed services |
| 9 | Trademark | “Orchestrator”, ND Estates marks only for official product; no “official Pro” claim on forks without permission |
| 10 | Term & termination | Term = paid period; non-renewal / revoke → Pro entitlement ends; Light/OSS use may continue under Apache for public code |
| 11 | Warranty disclaimer | Software “as is” to extent permitted by law (Jersey / applicable law) |
| 12 | Liability cap | Cap at fees paid in prior 12 months (or counsel default) |
| 13 | Governing law | Jersey (confirm) |
| 14 | Contact | licenses@ / support channel (no secrets in repo) |

### 2.2 Subscription Terms outline (placeholder)

| § | Topic | Draft intent |
|---|--------|--------------|
| 1 | Plans | Monthly £99; Annual £990 (10 months paid → 12 months access) — GBP; company scope |
| 2 | Payment | PayPal (or successor) on ndestates.io; taxes as applicable |
| 3 | Key issuance | After paid invoice / webhook: issue or renew hashed key; email delivery when live |
| 4 | Renewal | Auto-renew if productized; failed payment → grace then revoke (align with lease TTL) |
| 5 | Cancellation | End of period or immediate revoke on abuse; no refund policy TBD by counsel/ops |
| 6 | Changes | Price/plan changes with notice; grandfathering TBD |
| 7 | Support | Scope of support for Pro (response targets optional) |
| 8 | Data | Minimal account/billing data; point at privacy policy when portal live |
| 9 | Service availability | License validate API best-effort; offline Pro lease TTL already in product (e.g. 7–30d) |

### 2.3 Where these documents will live (when approved)

| Artifact | Location (proposed) | Public? |
|----------|---------------------|---------|
| Apache-2.0 | Root `LICENSE` | Yes |
| `NOTICE` (copyright + attributions) | Root `NOTICE` | Yes |
| Pro EULA | `docs/legal/ORCHESTRATOR-PRO-EULA.md` or website | Yes (customers) |
| Subscription Terms | `docs/legal/ORCHESTRATOR-PRO-SUBSCRIPTION.md` or website | Yes (customers) |
| This split plan | `docs/internal/OPEN-SOURCE-AND-PRO-LICENSE-SPLIT.md` | **No** |
| Current proprietary root LICENSE text | Superseded by Apache for OSS tree; salvage clauses into Pro EULA | — |

Do **not** commit real keys, admin tokens, or PayPal secrets. Placeholders only in docs.

### 2.4 Relationship to existing proprietary LICENSE

Root `LICENSE` today is an **ND Estates proprietary** agreement (evaluation, commercial key, first-party, reverse-engineering, competing product). On Apache adoption:

1. Replace root `LICENSE` with Apache-2.0 for the **public repository**.  
2. **Port** commercial intent (company key, no key resale, no circumventing **official** validation, trademark) into **Pro EULA §2**, not into the OSS root license.  
3. Drop or rewrite “no competing product that substantially reproduces skill/chain/loop system” if counsel finds it unenforceable against Apache recipients — rely on trademark + closed server + support instead where needed.

### 2.5 Enforcement (product, not only paper)

| Control | Status / note |
|---------|----------------|
| `LicenseGate` on `init` / `upgrade` | Exists |
| Light selection cap | Frozen in freemium product freeze |
| `POST /api/licenses/validate` | Contract stable |
| Production license-api + PayPal issue/revoke | Operator deploy still open (held PayPal go-live) |
| Official branding / docs “Buy Pro” | After messaging clear |

---

## 3. Keep closed — do not put under Apache public tree

Surfaces that **must stay private**, proprietary, or operator-only even after the public repo is Apache-2.0.

### 3.1 Hard closed (never publish in public OSS tree / packages)

| Surface | Why |
|---------|-----|
| Production **license-api** config, DO secrets, admin tokens | Key issue/revoke authority |
| **License key store** (SQLite/production DB), key hashes, customer emails | Personal + commercial data |
| **PayPal** live plan IDs, webhook secrets, client secrets | Payment integrity |
| **First-party allowlist** production keys / org lists beyond documented *policy* | Bypass surface |
| Customer license keys, trial keys, support tickets with PII | Confidential |
| Any `.env` / vault material for ndestates.io licensing | Secrets |
| Internal security deep catalogs if they expose attack paths beyond public posture | Need-to-know (`SECURITY-POSTURE` internal depth) |

Reference server **code** in-repo may remain as a **dev/reference** implementation under Apache if published — production **deployment, data, and credentials** stay closed. Prefer documenting “run your own” vs shipping ND Estates production endpoints in client defaults without operator consent.

### 3.2 Internal docs (exclude from release & public site)

Per `RELEASE-EXCLUSION.md` — keep out of npm `files`, PyPI package data, deploy-bundle defaults, and `docs/index.md`:

| Path / area | Notes |
|-------------|--------|
| `docs/internal/**` | Commercial plans, catalogs, this split doc |
| Freemium / PayPal wiring plans | Operator only |
| Skills/chains full internal catalogs | Public summary may live elsewhere; full inventory internal |
| Session/vault research dumps with customer residue | Scrub; do not open-source |

### 3.3 Soft closed (public code OK, production stay private)

| Surface | Public code? | Production closed? |
|---------|--------------|--------------------|
| `src/orchestrator_cli/license_server.py` + CLI | Yes (reference) | Yes (your deploy) |
| `services/license-api/` scaffold | Yes (template) | Yes (app spec secrets, volumes) |
| `docs/reference/licensing.md` | Yes (field names, placeholders) | N/A — no real URLs/keys |
| Light vs Pro selection policy | Yes (documented behaviour) | N/A |
| First-party **remote detection policy** | Yes (mechanism) | Org-specific lists private |

### 3.4 Public-OK (Apache candidates)

| Surface | Notes |
|---------|--------|
| CLI init/upgrade/check (gate client) | Gate is client-side; server enforces Pro |
| Skills, chains, loops, scripts, cache-spine (Light set) | Core OSS value |
| Broader skill tree if you choose open-core full tree | Accept fork risk |
| Install scripts, README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT | Standard OSS |
| Public security / guardrails references | Already operator-facing |
| Tests for license **client** behaviour | No production keys |

### 3.5 Inventory checklist (open-source readiness)

Use before first public Apache tag:

- [ ] Root `LICENSE` → Apache-2.0 + copyright line confirmed  
- [ ] `NOTICE` if needed  
- [ ] SPDX on `pyproject.toml` / `package.json`  
- [ ] Scan for hardcoded production license URLs or keys  
- [ ] Confirm `docs/internal/**` not in package `files` / wheel  
- [ ] Public README states: Apache core + optional Pro subscription (link EULA when live)  
- [ ] Patreon pitch does **not** promise Pro keys unless productized  
- [ ] Pro EULA + Subscription Terms drafted with counsel (§2)  
- [ ] Trademark note in README or NOTICE  
- [ ] Decision: is `services/license-api/` fully public scaffold only (yes recommended)

---

## 4. Messaging (draft — public README later)

**One paragraph (intent):**

> Orchestrator’s public codebase is licensed under **Apache License 2.0**. **Orchestrator Light** is free for limited install selections. **Orchestrator Pro** is a paid company subscription (£99/month or £990/year) that unlocks full selections via a license key and is governed by the Orchestrator Pro EULA and Subscription Terms. Cloud AI tools are separate subscriptions. Support the project on Patreon if you wish — patronage is optional and is not a Pro license unless we say so explicitly.

---

## 5. Next actions (this branch / counsel)

| # | Action | Owner | Blocker |
|---|--------|-------|---------|
| 1 | Human approve this split (EULA path + closed inventory) | Operator | — |
| 2 | Counsel review §2 outlines → real EULA/Subscription | Counsel | Jersey entity details |
| 3 | Apache-2.0 root LICENSE + NOTICE draft on branch | Eng | Copyright holder string |
| 4 | Align `docs/reference/licensing.md` with OSS + Pro EULA model | Eng | After public wording OK |
| 5 | Patreon prep copy (funding ≠ key) | Operator | — |
| 6 | Hold live PayPal until asked | Ops | Explicit unhold |

---

## 6. Document history

| Date | Change |
|------|--------|
| 2026-07-22 | Initial draft: §2 Commercial EULA + Subscription; §3 Keep closed inventory |
