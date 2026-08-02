# Stronger with every update (agent reference)

**Mandatory standard (2.0.0+).** Full doc: `docs/reference/stronger-with-every-update.md`  
Trust map: `SECURITY.md` · Chrome: https://blog.google/security/chrome-stronger-with-every-update/

## Life of a bug (do all five)

1. **Find** — bug-hunter / security-audit / mcp-threat-scan / session-security-sweep  
2. **Triage** — severity, area, not duplicate → vault + memory lesson  
3. **Fix** — patch + tests; **critic ≠ author** (code-review / loop-verifier)  
4. **Release** — version path, changelog, bundle-hash if high-risk  
5. **Apply** — host self-upgrade offer; per-app upgrade carefully (**no broadcast**)

## Rules

- Found ≠ fixed. Fixed ≠ applied.  
- Multi-model OK for finding (full catalog); high-risk stays human-gated.  
- AI analysis fenced (sandbox, scrub, no unrestricted).  
- Prefer class elimination (guardrails, secrets hooks, MCP off by default).  
- No cozy workspace — do not skip scans “because we know this tree.”

## Session-start

Cite security sweep + surface open security items from vault/memory. Offer upgrade when tip lags.
