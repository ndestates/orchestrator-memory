# License API (MVP) — optional / advanced

> **Product note (2026-08-01):** Orchestrator public releases are **Apache-2.0 freeware**.  
> This API is **not** required for end users. Keep it only if you run a **private** entitlement gate.  
> Optional project support: Patreon donations — not software keys. See `docs/reference/licensing.md`.

Production-oriented packaging of `orchestrator_cli.license_server` for **DigitalOcean App Platform**.

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/healthz` | none |
| POST | `/api/licenses/validate` | optional Bearer / body key |
| POST | `/api/licenses/issue` | admin Bearer |
| POST | `/api/licenses/revoke` | admin Bearer |

## Product freeze (v1)

| SKU | Price | Scope |
|-----|-------|--------|
| **Light** | Free | Deploy selections: `grok,chains,loops,scripts,cache-spine` |
| **Pro monthly** | **£99 / month** | **One key per company** (not per seat) |
| **Pro annual** | **£990 / year** | Same key; **2 months free** (10× monthly) |

## Local

```bash
export ORCHESTRATOR_LICENSE_DB=/tmp/orch-licenses.sqlite3
export ORCHESTRATOR_LICENSE_ADMIN_TOKEN=dev-admin-token
PYTHONPATH=src python3 -m orchestrator_cli.license_server

# Issue Pro company key
curl -sS -X POST http://127.0.0.1:8787/api/licenses/issue \
  -H "Authorization: Bearer dev-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"tier":"pro","email":"ops@example.com","note":"manual"}'
```

## DigitalOcean

1. Create App from `app.yaml` (or UI) with repo root as source.
2. Set secret `ORCHESTRATOR_LICENSE_ADMIN_TOKEN`.
3. Prefer a **persistent volume** on `/data` for SQLite (or managed Postgres later).
4. Custom domain later: `licenses.ndestates.io`.
5. Client:

```bash
export ORCHESTRATOR_LICENSE_URL=https://<your-app>.ondigitalocean.app/api/licenses/validate
export ORCHESTRATOR_LICENSE_KEY=orch_...   # from issue response
orchestrator license
```

**Do not** commit real keys or admin tokens.
