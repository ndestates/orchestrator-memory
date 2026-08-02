# Free light + £99 Pro license + license server — feasibility & plan

**Branch:** `feature/freemium-license-publish-2026-07-18`  
**Date:** 2026-07-17 (updated 2026-07-18)  
**Status:** Feasible — **yes**. Product freeze + server MVP + publish path started.  

**Freeze decisions:** see `docs/internal/FREEMIUM-PRODUCT-FREEZE.md`  
- Light free selections frozen  
- **Pro = £99/month per company**; annual = pay 10 months get 12 (2 free)

> Internal commercial/engineering plan. Not for public docs site.

**License architecture (2026-07-22):** Public OSS core → Apache-2.0 (planned). Paid Pro → **Commercial EULA + Subscription Terms**. Closed inventory (license-api prod, keys, PayPal secrets, `docs/internal/**`) → do not Apache. Full split: [`OPEN-SOURCE-AND-PRO-LICENSE-SPLIT.md`](./OPEN-SOURCE-AND-PRO-LICENSE-SPLIT.md).

---

## 1. Feasibility: **Yes**

You already have most of the **product plumbing**:

| Piece | Exists today |
|-------|----------------|
| Free vs full **entitlements** | `TRIAL_LITE` / `PRO_FULL` in `licensing_policy.py` |
| Deploy **selection caps** for lite | `defaults.TRIAL_SELECTION_NAME = "trial"` |
| CLI gate on init/upgrade | `LicenseGate` → `POST …/api/licenses/validate` |
| Lease model | In-memory TTL; server returns `tier` (`trial` \| `pro`), `is_first_party` |
| **Reference license server** | `orchestrator license-server` / `license_server.py` (stdlib HTTP) |
| Fail-open without server | Gate **off** when `ORCHESTRATOR_LICENSE_URL` unset (good for OSS light) |
| First-party bypass | Org remotes / allowlist keys (ndestates) |
| Docs contract | `docs/reference/licensing.md` (path + JSON shape) |

What you **do not** have yet for a shoppable £99/mo Pro product:

- A **production** issuer (store keys, Stripe/PayPal checkout, email delivery)  
- **Published** free vs pro packages (or one package + server-enforced selections)  
- Default **public** validate URL baked into Pro builds  
- Operator UI (even minimal) to issue/revoke keys  
- Hard product definition of what “light” includes  

Hosting on **DigitalOcean App Platform** or **ndestates.io** (when live) is straightforward: one small HTTPS service with the **same** `POST /api/licenses/validate` contract.

---

## 2. Product model (recommended)

### 2.1 Two tiers (map to existing enums)

| SKU | Price | Entitlement | What they get |
|-----|-------|-------------|----------------|
| **Orchestrator Light** | **Free** | `TRIAL_LITE` (UX → **Light**) | Cache-first session tools, core skills, session-start envelope, limited deploy **selections** |
| **Orchestrator Pro** | **£99 / month** per company; **annual = 10× monthly (£990)** for 12 months (**2 months free**) | `PRO_FULL` | Full deploy selections, full skill/agent surface, MCP package, wiki, upgrade verify-bundle |

**Payment:** Stripe subscription (monthly or annual) → generate **license key** → customer sets `ORCHESTRATOR_LICENSE_KEY`. Failed renewal → revoke or grace period.

**Scope:** one key per **company** (not per seat).

### 2.2 Packaging options (pick one for v1)

| Option | How | Pros | Cons |
|--------|-----|------|------|
| **A. One package + license unlocks Pro** (recommended) | Single npm/PyPI artifact; light works offline/fail-open or with light defaults; Pro requires valid key against license server | One build pipeline; simpler for you | Need clear UX when key missing |
| **B. Two packages** | `@ndestates/orchestrator` (light) + `@ndestates/orchestrator-pro` | Marketing clarity | Two publish paths; drift risk |
| **C. Open source light git only + paid Pro wheel** | Light = GitHub; Pro = private registry | Stronger paywall | Friction for free users |

**Recommendation: A** — one public install path; **server + key** gate Pro selections on `init`/`upgrade`. Light selections always allowed without key (or with anonymous light lease).

### 2.3 What Light vs Pro control technically

Enforcement point (already in flow): **`orchestrator init` / `upgrade`** → `enforce_for_flow` → `resolve_flow_selections(entitlement)`.

| Capability | Light | Pro |
|------------|-------|-----|
| `check` / `status` / `version` | Yes | Yes |
| Session-start scripts (envelope, resume) after init | Yes (shipped in light selections) | Yes |
| Full `.grok` skills / all agents | No (capped selections) | Yes |
| MCP server deploy selection | No | Yes |
| Wiki selection | No | Yes |
| `deploy-bundle` full selections | No | Yes |
| Fleet wave | **Neither** (deleted) | **Neither** |

Exact selection strings must match `scripts/deploy-bundle.yaml` (define `trial` / `light` selection if missing).

---

## 3. License server architecture (efficient)

### 3.1 API contract (keep existing — do not invent a second protocol)

**Validate (already implemented by clients):**

```http
POST /api/licenses/validate
Content-Type: application/json
Authorization: Bearer <LICENSE_KEY>   # optional if also in body

{ "license_key": "<LICENSE_KEY>" }
```

**Success (shape CLI already parses):**

```json
{
  "valid": true,
  "ttl": 86400,
  "is_first_party": false,
  "tier": "pro",
  "allowed_selections": null
}
```

**Light without key (optional server path):** either  
- no call (local light defaults), or  
- `tier: "trial"` + `allowed_selections: ["light", "scripts"]`.

**Failure:** `{ "valid": false, "error": "…" }` → CLI deny Pro actions.

### 3.2 Where to host

| Host | When | How |
|------|------|-----|
| **DigitalOcean App Platform** (recommended **now**) | ndestates.io not published | Small Docker/Python service; env secrets; HTTPS; custom domain later `licenses.ndestates.io` |
| **ndestates.io** (recommended **later**) | Portal goes live | Same path under `https://ndestates.io/api/licenses/validate`; issue UI + Stripe Checkout on portal |
| **DO Droplet** | Only if you need long-lived DB control | More ops; avoid for v1 |

**v1 server can be thin:**

1. **Phase 1 (weeks):** Hardened fork of `license_server.py` + **Postgres/SQLite** table of keys (`key_hash`, tier, email, issued_at, revoked, note). Issue keys via CLI/admin script or DO console one-shot.  
2. **Phase 2:** Stripe Subscriptions (£99/mo + £990/yr) → webhook → insert/renew key → email.  
3. **Phase 3:** ndestates.io admin UI + customer “my license” page.

**Do not** put real keys in the orchestrator git repo. Store only **hashes** (SHA-256 of key) on the server.

### 3.3 Issue flow (subscription £99/mo or £990/yr)

```text
Customer subscribes (£99/mo or £990 annual = 10× monthly / 2 months free)
  → webhook invoice.paid: create or renew license_key, store hash, tier=pro
  → email key + install instructions (first payment only)
Customer:
  export ORCHESTRATOR_LICENSE_KEY=…
  export ORCHESTRATOR_LICENSE_URL=https://licenses.ndestates.io/api/licenses/validate
  orchestrator upgrade /path/to/app
  → POST validate → lease tier=pro → full selections
Cancel / failed payment → revoke or grace → Light only
```

**Offline grace:** keep Pro lease TTL (e.g. 7–30 days) so brief network loss does not brick paid users. Light needs no network.

### 3.4 Security (minimum bar)

| Control | Detail |
|---------|--------|
| TLS only | App Platform terminates TLS |
| Rate limit | Per IP on `/validate` (abuse) |
| Key storage | Hash only; show key once at issue |
| No secrets in client | Only URL + user key in env |
| Audit log | validate ok/fail counts (no raw keys) |
| First-party | Separate keys or git-remote allowlist for ND Estates apps (already conceptually supported) |
| Revocation | `revoked_at` on row → validate returns invalid |

---

## 4. Workable phased plan (efficient)

### Phase 0 — Product freeze (½ day)

- [x] Write **Light selection set** (`LIGHT_SELECTIONS` + deploy aliases `light`/`trial`/`free`)  
- [x] Table: which skills/agents/MCP/wiki are Pro-only (`PRO_ONLY_SELECTIONS` + freeze doc)  
- [x] **£99/mo company key** (not per seat); **annual = 10 months paid / 12 months access**

### Phase 1 — Server MVP on DigitalOcean (2–4 days)

- [x] Repo service: `services/license-api/` (Dockerfile + app.yaml)  
- [x] SQLite volume path via `ORCHESTRATOR_LICENSE_DB`  
- [x] Endpoints: validate + issue + revoke (admin token)  
- [ ] Deploy App Platform + `licenses.<domain>` or temporary `*.ondigitalocean.app` (operator)  
- [ ] Seed first-party keys for ND Estates (operator)  
- [ ] Smoke: local CLI against production URL with test Pro key (operator)  

Reuse: protocol from `src/orchestrator_cli/license_server.py` + tests in `tests/test_license_validate_server.py` / mcp license tests.

### Phase 2 — Client productisation (2–3 days)

- [ ] Rename UX strings trial → **Light** (keep enum compat)  
- [ ] Default `ORCHESTRATOR_BUILD_DEFAULT_LICENSE_URL` in **release** wheels only  
- [ ] Clear messages: “Light mode (free). Pro £99/mo or £990/yr (2 mo free): &lt;url&gt;”  
- [ ] `orchestrator license` shows tier + expiry  
- [ ] Fail **closed for Pro selections** when URL set and key invalid; Light selections still work  

### Phase 3 — Commerce (2–5 days)

- [ ] Stripe Subscriptions: **£99/month** + **£990/year** (10× monthly = 2 months free)  
- [ ] Webhook → issue key on first paid invoice; renew/cancel → extend or revoke  
- [ ] Email key + install instructions  
- [ ] VAT: consult accountant; Stripe Tax optional later  

### Phase 4 — Packages + install path (ties to app-installable work)

- [ ] Publish free package to npm/PyPI  
- [ ] Document: free install without key; Pro with key  
- [ ] PowerShell/bash install CLI from registry  
- [ ] VS Code extension: Status shows Light/Pro  

### Phase 5 — ndestates.io portal (when site exists)

- [ ] Move/alias validate to `https://ndestates.io/api/licenses/validate`  
- [ ] Customer dashboard: view key (or re-issue once), invoices  
- [ ] Deprecate temporary DO hostname with redirect  

---

## 5. Efficient defaults (avoid gold-plating)

| Do | Don’t |
|----|--------|
| One validate endpoint, existing JSON | Custom crypto license files for v1 |
| Hash keys in DB | Store plaintext keys |
| Stripe Subscriptions (mo + annual) | Build full cart v1 |
| App Platform + managed DB | Kubernetes |
| Enforce on **init/upgrade** only | Block every skill run online (too harsh, offline-hostile) |
| Long Pro lease TTL (e.g. 30d refresh) | Phone-home every command |
| Delete wave forever | Sell “enterprise wave” |

---

## 6. Relationship to “drop wave + app installable”

| Track | Dependency |
|-------|------------|
| Drop wave | Independent — do first or in parallel |
| npm/PyPI publish | Required so free Light is installable without git |
| License server | Required before marketing Pro £99/mo |
| ndestates.io | Nice host for UI; **not** blocking if DO hosts API first |

Suggested sequence on this branch:

1. Kill wave (no commercial value in multi-app free fleet)  
2. License server MVP + Light selections  
3. Publish packages + Pro checkout  
4. VS Code extension  

---

## 7. Cost sketch (order of magnitude)

| Item | Monthly-ish |
|------|-------------|
| DO App Platform small + DB | ~£10–30 |
| Domain / DNS | existing Route53 |
| Stripe fees | ~1.5% + fixed per charge (£99 mo or £990 yr) |
| Email | free tier → low paid |

Engineering: ~1–2 weeks calendar for Phases 0–3 if focused; portal later.

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Key sharing | ToS + optional machine fingerprint later (not v1) |
| Offline Pro users | Long lease; clear error only when refreshing |
| PyPI name `orchestrator` taken | Publish as `ndestates-orchestrator` if needed |
| Light too generous | Tight `light` selection; review quarterly |
| Server outage | Fail-open for Light only; Pro use last good lease until TTL |

---

## 9. Acceptance criteria (done when)

- [ ] Free user: install from registry, `upgrade` with light selections, no payment  
- [ ] Paid user: subscribes £99/mo or £990/yr, receives key, `tier=pro`, full selections on upgrade  
- [ ] Invalid/revoked key cannot pull Pro selections  
- [ ] ND Estates first-party apps unblocked  
- [ ] Validate URL production HTTPS, rate-limited  
- [ ] No wave path remains  
- [ ] Docs: buy/install/license check for operators  

---

## 10. Immediate next actions

1. Confirm **Light selection list** (product call — 1 hour)  
2. Confirm **company scope** (done) + **monthly + annual with 2 free months** (done)  
3. Spin **DO App Platform** license-api + DB  
4. Wire release build `DEFAULT_LICENSE_URL`  
5. Stripe Subscriptions → issue/renew/revoke webhooks  

---

## 11. Code anchors (do not reimplement from scratch)

| File | Role |
|------|------|
| `src/orchestrator_cli/licensing_policy.py` | Entitlements `TRIAL_LITE` / `PRO_FULL` |
| `src/orchestrator_cli/license.py` | Client gate + lease |
| `src/orchestrator_cli/license_server.py` | Reference validate server |
| `src/orchestrator_cli/defaults.py` | `TRIAL_SELECTION_NAME`, optional default URL |
| `src/orchestrator_cli/flow.py` | Enforce on init/upgrade |
| `docs/reference/licensing.md` | Public contract (no prices) |
| `mcp-server` license gate | Align MCP with same URL/key |

---

**Bottom line:** Feasible and efficient if you treat **Light = free selection cap**, **Pro = £99/mo company subscription (annual 2 months free) + existing validate API**, host the small server on **DigitalOcean now**, move UI to **ndestates.io later**, and ship packages so apps never need the monorepo or wave.
