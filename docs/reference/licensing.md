# Licensing (freeware)

[UPDATED 2026-08-01] — **Apache-2.0 freeware** · donations via Patreon (optional)

## Product policy

| | |
|--|--|
| **Software license** | **[Apache License 2.0](../../LICENSE)** — free open source |
| **Cost to use** | **£0** — no paid tier required for CLI, memory, skills, VS Code extension, or full deploy selections |
| **Support the project** | **Optional** [Patreon](https://www.patreon.com/ndestates) (or your published page) — **donations only**, never a license key |
| **Attribution** | Keep copyright + LICENSE notices when you redistribute (Apache requirement) |

There is **no Pro / Light product split** for end users. Paid £99 “Pro company keys” are **retired as a product model** in favour of free OSS + optional patronage.

See also: [NOTICE](../../NOTICE) · [Production ship](../guides/production-ship.md)

---

## Why Apache-2.0 (not proprietary / not “all rights reserved”)

| Need | Apache-2.0 |
|------|------------|
| Freeware use | Yes — use, modify, ship |
| Commercial use of *your* apps built with it | Yes |
| Patent peace-of-mind for contributors/users | Explicit patent grant |
| Compatible with npm / PyPI / VS Code | Yes |
| Require payment for features | **No** — that would not be freeware OSS |

MIT is also fine for freeware; **Apache-2.0** is the better fit for a multi-contributor tooling product (patent grant + clear NOTICE practice). This matches the long-standing “open-source Apache + Patreon” track.

---

## Optional Patreon (donations)

Patrons may get thank-yous, early notes, or community access **you** define off-repo.  
Patronage **does not**:

- unlock code that free users lack  
- replace Apache rights  
- act as a software license key  

Set your public URL in:

- README “Support” section  
- `.github/FUNDING.yml`  
- This page  

Default placeholder: `https://www.patreon.com/ndestates` — change if your page differs.

---

## Optional self-hosted license server (advanced / internal)

The repo still contains **`orchestrator license`**, **`license-server`**, and `services/license-api/` for operators who want **their own** entitlement gates on *forks* or internal distributions.

| Mode | Behaviour |
|------|-----------|
| **Default (freeware)** | `ORCHESTRATOR_LICENSE_URL` **unset** → gate **off** → full free use |
| **Optional enforce** | Set `ORCHESTRATOR_LICENSE_URL` yourself if you run a private gate |

**Official ND Estates product distribution:** do **not** require a paid key for Apache-published releases. Gate remains fail-open / off for public freeware.

Historical notes on freemium pricing live under `docs/internal/` (superseded for product positioning).

### Check gate status

```bash
orchestrator license
# Expected (freeware default): gate disabled / local use allowed
```

### Run reference server (only if you need it)

```bash
orchestrator license-server
# or: PYTHONPATH=src python3 -m orchestrator_cli.license_server
```

Env names (when you deliberately enable a private gate):  
`ORCHESTRATOR_LICENSE_URL`, `ORCHESTRATOR_LICENSE_KEY`, `ORCHESTRATOR_LICENSE_DB` — see code comments; no secrets in this doc.

---

## What you may do (plain language)

Under Apache-2.0 you may:

- Install host CLI (uv / pip / npm) and use `orchestrator memory` on any project  
- Install the VS Code extension  
- Fork, modify, and redistribute (with license notices)  
- Use commercially in your business **without** paying us  

You should **not** remove license/copyright notices from redistributed copies.

---

## Related

- [Installation](../getting-started/installation.md)  
- [Production ship](../guides/production-ship.md)  
- [SECURITY.md](../../SECURITY.md) — still applies; freeware ≠ insecure  
