# Standard — Stronger with every update

[UPDATED 2026-07-31] · **Product 2.0.0+** · **Mandatory security standard**

Inspired by Google Chrome’s doctrine  
[Stronger with every update](https://blog.google/security/chrome-stronger-with-every-update/)  
(Chrome Security Team, 2026 — AI-era vulnerability lifecycle).

**Companion tenets:** [No cozy workspace](../internal/SECURITY-POSTURE.md) §0 · AI content guardrails · always-on memory.

---

## 1. One-line standard

**Every orchestrator release and session must leave the operator safer than before** — not by accumulating security theatre, but by **shortening the life of a security bug** and **eliminating whole classes of failure**.

An increase in bugs found/fixed is **not** failure. Every fix is one less attacker foothold — *if* it is shipped and applied.

---

## 2. Life of a bug (orchestrator mapping)

Chrome’s five steps → our concrete surfaces:

| Step | Chrome idea | Orchestrator standard |
|------|-------------|------------------------|
| **1. Find** | AI + fuzzing + external research | `bug-hunter` · `security-audit` · `mcp-threat-scan` · `malware-lint` · `session-security-sweep` · CSE · multi-model catalog (OSS + free + frontier) |
| **2. Triage** | Filter noise → reproduce → enrich → assign | L1 report-only first · severity + area in vault/memory · route to specialist agent · no silent auto-merge of high risk |
| **3. Fix** | Fix agent ↔ critic loop + tests | Fix proposal → `code-review` / `loop-verifier` critic → `test-specialist` + `test-safety` · never untested security fix |
| **4. Release** | Shrink patch gap | Tag + host package + per-app upgrade path · bundle-hash verify · changelog + vault lesson |
| **5. Apply** | Silent / low-friction updates | `self-upgrade` / `ensure` · session-start upgrade **offer** · install-persist · never multi-branch blast |

**Speed goal:** find → triage → fix → ship → apply must outpace N-day exploitation. Prefer **small frequent upgrades** over rare mega-diffs.

---

## 3. Non-negotiable rules (agents + humans)

1. **Bug found is not safety.** Safety requires **released + applied** on the tip the operator runs.
2. **Minimize the patch gap.** Prefer host CLI upgrade + app `upgrade --quiet` over leaving operators on stale locks.
3. **Multi-model finding.** Vulnerability work may use **all** catalog models (OSS/local + free_cloud + host frontiers) — same rule as always-on memory. High-risk remains frontier / human-gated.
4. **Finder ≠ fixer ≠ critic.** Separate contexts when practical (Chrome “critic agent”). Use verifier/code-review that did not author the patch.
5. **Knowledge base of past bugs.** SECURITY boundaries, vault lessons, always-on memory, and `SECURITY.md` (this repo) feed agents — never re-discover the same class blindly.
6. **AI scans stay fenced.** Analyze at rest; sandbox paths; no unrestricted tools; scrub untrusted text; MCP dev-only on public hosts.
7. **Prevention > endless cure.** Prefer class elimination (guardrails, sandbox, type-safe paths, secrets hooks) over only patching instances.
8. **Dependencies stay fresh.** Prefer automated, guarded updates of tooling deps; verify bundle integrity on template upgrade.
9. **Disclosure discipline.** Security-relevant fixes land in changelog/session notes without secret leakage.
10. **No cozy workspace.** Expertise does not skip steps 1–5.

---

## 4. AI-era finding & triage (what we operationalize)

From Chrome’s playbook, adopted for this template:

| Practice | How we do it |
|----------|----------------|
| Model interoperability | `scripts/model-route/catalog.yaml` + memory/security agent routing |
| Knowledge beyond training | Vault + always-on memory + docs/codebase cache + this SECURITY.md |
| Trust-boundary docs | This file + `docs/internal/SECURITY-POSTURE.md` + skill references |
| Critic with separate context | `loop-verifier` · `code-review` · independent subagent |
| Repeated scans | Session sweep · pre-release gate · CI workflows · optional L1 watches |
| Guardrailed AI | untrusted_text · MCP sandbox · no auto high-risk fix without approval |

---

## 5. Session & release checklists

### Every `/chain session-start`

- [ ] Security sweep cited (PASS/WARN/FAIL)
- [ ] Vault + memory brief (recent security lessons)
- [ ] Version matrix / upgrade offer if host or apps lag (offer only — never silent)
- [ ] On remote_last / team tip when clean (patch applies to the real tip)

### Every security-relevant change

- [ ] Find or accept external report with clear repro/summary
- [ ] Triage: severity, area, duplicate check → vault/memory lesson
- [ ] Fix + tests + critic review
- [ ] Release path + bundle-hash if high-risk paths touched
- [ ] Apply path documented for apps (`upgrade` + `install-persist`)

### Every `/chain eod-shutdown`

- [ ] Security lessons dual-written (vault; memory when enabled)
- [ ] Resume card states open security work honestly

---

## 6. Class elimination (prefer these over one-off patches)

| Class | Orchestrator control |
|-------|----------------------|
| Prompt injection / instruction smuggling | `untrusted_text` · content guardrails · untrusted path policy |
| Secrets in git | git-push-secrets-guard · session sweep |
| Hostile MCP / skill grants | mcp-threat-scan · skill-governance |
| Supply-chain tamper | bundle-hashes + upgrade verify |
| Live DB destruction | test DB only · DDEV local runtime |
| Cosy overconfidence | SECURITY-POSTURE §0 |
| Stale host/app versions | version alignment · self-upgrade · upgrade offers |

---

## 7. What this is *not*

- Not a claim of certification (CSE remains lean gap-scan unless full review requested)
- Not permission to auto-apply high-risk patches without human gate
- Not fleet-wide silent upgrade (no wave/broadcast by default)
- Not “more bugs = worse product” — **unfixed / unapplied** is worse

---

## 8. References

- Source doctrine: [blog.google — Stronger with every update](https://blog.google/security/chrome-stronger-with-every-update/)
- Internal depth: `docs/internal/SECURITY-POSTURE.md`
- Guardrails: `.grok/references/ai-content-guardrails.md`
- Always-on memory: `docs/guides/always-on-memory.md`
- Host-first install: `docs/guides/host-first-memory.md`
- Version clocks: `docs/reference/versioning.md`
- Manifest: `security_policy.stronger_with_every_update`
- License: **Apache-2.0** freeware (`LICENSE`, `NOTICE`)
