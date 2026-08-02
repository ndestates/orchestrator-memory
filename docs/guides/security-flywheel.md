# Security flywheel (Chrome-style, template + apps)

[UPDATED 2026-08-01] · **Apache-2.0** · product **2.0.0+**

**Idea:** [Chrome — Stronger with every update](https://blog.google/security/chrome-stronger-with-every-update/)  
**Canonical doctrine:** [`docs/reference/stronger-with-every-update.md`](../reference/stronger-with-every-update.md)  
**Trust map:** root [`SECURITY.md`](../../SECURITY.md)

This is the **same flywheel** already running on **ndestates** and **lightstone** (interdependent). The orchestrator template now ships the host scripts + chain so every app can run the lifecycle without inventing it again.

We do **not** copy Chrome’s C++/Gemini vuln farms. We encode **find → triage → fix → ship → prevent** into tools you already have.

---

## Lifecycle

```text
  FIND ──► TRIAGE ──► FIX ──► SHIP ──► PREVENT
    ▲                                    │
    └──── vault + always-on memory ──────┘
```

| Stage | Tools (orchestrator) | App extras (Laravel) |
|-------|----------------------|----------------------|
| **Find** | `security-flywheel-status.sh`, session sweep, mcp-threat-scan, dependabot, bug-hunter | Pest red-team, app CE checklist |
| **Triage** | SECURITY.md S0–S3, vault lessons, memory ingest | CONCERNS, app TODO |
| **Fix** | Small PR + tests; code-review critic ≠ author | DDEV + test DB only |
| **Ship** | feature → develop → release; self-upgrade host; per-app upgrade carefully | staging smoke → promote |
| **Prevent** | MCP off default, secrets guard, bundle-hash, always-on memory | MFA, headers/CSP, fail-closed APIs |

---

## Commands

```bash
# Dashboard (any repo with these scripts)
bash scripts/security-flywheel-status.sh
bash scripts/security-flywheel-status.sh --quick
bash scripts/security-flywheel-status.sh --peers   # ndestates ↔ lightstone
bash scripts/security-flywheel-status.sh --json

# L1 host snapshot for loops/CI
bash scripts/loop-security-flywheel-host.sh
bash scripts/loop-security-flywheel-host.sh --full --peers

# Agent depth
/chain security-flywheel

# Optional: put outcome in always-on memory (not the vault DB — dual-write only)
orchestrator memory ingest --text "flywheel RESULT=…" --source flywheel
```

Report: `reports/security/flywheel-status-YYYY-MM-DD.md`

---

## Interdependence (ndestates ↔ lightstone)

Both apps share:

1. Same lifecycle language (S0–S3, find→prevent)  
2. `SECURITY.md` + flywheel guide + status script  
3. Peer checks via `scripts/security/flywheel-peers.yaml`

When you change a shared control (e.g. apply-forms auth, Lightstone tokens, CSP path):

1. Run flywheel status on **both** peers (`--peers` from orchestrator or each app).  
2. Triage FAIL on either as ship-blocking.  
3. Ship small fixes to both trees; do not leave one green and one lagging.  
4. EOD: vault lesson + optional memory ingest so session-start does not re-open fixed work.

Peers file (template default):

```yaml
# scripts/security/flywheel-peers.yaml
peers:
  - path: ../ndestates
  - path: ../lightstone
```

---

## Chain: `/chain security-flywheel`

1. **load** — cache-first spine + SECURITY.md + this guide  
2. **status** — `security-flywheel-status.sh` (FAIL→S0/S1, WARN→S2)  
3. **ce** — cyber-security-essentials lean  
4. **audit** — security-audit-agent (report-only unless user asks fix)  
5. **prevent** — summarise class controls + next ship bar  

No auto-fix at L1.

---

## Session / loop

| Moment | Behaviour |
|--------|-----------|
| **session-start** | Security sweep already runs; cite flywheel if open S0–S2 |
| **loop watch** | `security-flywheel-watch` L1 host snapshot (Monday-style) |
| **EOD** | Resume card lists open security FAIL/WARN |
| **memory** | Optional ingest of flywheel results; vault remains `events.jsonl` |

---

## What we skip (on purpose)

| Chrome | Why not 1:1 |
|--------|-------------|
| Unrestricted AI mutators in CI | Report-first unless human asks fix |
| Memory-safe language rewrite | PHP/Laravel apps; template is tooling |
| Browser Stable cadence | develop → release; host `self-upgrade` |

---

## Related

- [Host-first memory](host-first-memory.md)  
- [Stronger with every update](../reference/stronger-with-every-update.md)  
- [Cyber Essentials skill](../../.grok/skills/cyber-security-essentials/SKILL.md)  
- Pattern: `patterns/security-flywheel-watch.md`
