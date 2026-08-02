# Plan: WebMCP beta setup (orchestrator)

**Branch:** `feature/webmcp-beta-setup-2026-07-21`  
**Base:** `origin/develop`  
**Status:** Active  
**Maturity:** **Beta / experimental** — Chrome origin trial + flag; APIs can change  
**Multi-workstream session v2:** **ACTIVE** on `feature/multi-workstream-session-v2-2026-07-22` (merged WebMCP here)

---

## 1. Goal

Add a **beta, opt-in WebMCP** track to the orchestrator template so operators and app repos can:

1. Understand **WebMCP vs host MCP** (browser page tools ≠ `orchestrator-host` stdio MCP).
2. Scaffold / document page tools (`navigator.modelContext.registerTool` / declarative form attrs).
3. Wire **local try path** (Chrome flag, inspector extension) and **origin-trial** notes.
4. Point at existing demos (Sarah Drasner demo, local `webmcp-demo`, Chrome Labs demos).
5. Stay **lean and non-default** — no required runtime, no public-host MCP, no multi-session SDK.

**Not in scope:** multi-workstream session spine; freemium/PayPal; vector DB; porting multi-session SDK.

---

## 2. Context (facts)

| Item | Detail |
|------|--------|
| Spec / explainer | [webmachinelearning/webmcp](https://github.com/webmachinelearning/webmcp) |
| Chrome docs | [developer.chrome.com/docs/ai/webmcp](https://developer.chrome.com/docs/ai/webmcp) — Origin trial (Chrome 149+), Intent to Experiment |
| Local flag | `chrome://flags/#enable-webmcp-testing` |
| Inspector | Chrome Web Store “Model Context Tool Inspector” (`gbpdfapgefenggkahomfgkhfehlcenpd`) |
| Pedagogy demo | [webmcp-demo-sdras.netlify.app](https://webmcp-demo-sdras.netlify.app/) |
| Local fork | `~/projects/webmcp-demo` (static site + orchestrator overlay; `navigator.modelContext` + localRegistry fallback) |
| Orchestrator host MCP | `mcp-server/`, `ensure-mcp-host.sh`, `mcp_policy=dev_only` — **different layer** |

**API surface (beta):**

- **Imperative:** `navigator.modelContext.registerTool({ name, title, description, inputSchema, execute, … })`
- **Declarative:** HTML form attrs (`toolname`, `tooldescription`, `toolparamdescription`, …)
- Security: origin isolation; Permissions-Policy `tools`; user still in loop; no headless tool calls

---

## 3. Product principles

1. **Beta badge everywhere** — skills, guides: `experimental` / `beta`; APIs may break.
2. **Do not conflate with host MCP** — WebMCP = in-page tools for browser agents; host MCP = develop-only cache/TODO tools.
3. **Progressive enhancement** — sites must work without WebMCP (localRegistry / feature-detect fallback).
4. **Security first** — secure-tools guidance; tool descriptions/args as untrusted DATA (`ai-content-guardrails`).
5. **Opt-in only** — no auto-enable in session-start; no install on public hosts.
6. **App work stays in apps** — template ships skill + guide + snippets; live demos stay in `webmcp-demo` (or other apps).

---

## 4. Deliverables

| Phase | Deliverable |
|-------|-------------|
| 0 | Branch from `origin/develop` |
| 1 | Plan, operator guide, index links, literacy + host-MCP cross-links, TODO |
| 2 | `/webmcp-beta` skill, references, optional `webmcp-setup` chain |
| 3 | Snippets under skill `references/` (not forced deploy-bundle) |
| 4 | Optional dogfood in sibling `webmcp-demo` (only on explicit ask) |

---

## 5. Non-goals

| Non-goal | Why |
|----------|-----|
| Multi-workstream session v2 | Active on multi-workstream branch (merged) |
| Default session-start WebMCP | Beta + browser-only |
| Chrome extension in template | Third-party / store |
| Headless WebMCP in CI | Spec requires browsing context |
| Replacing `orchestrator-host` MCP | Different layer |
| Production OT tokens in template | Per-origin; operator registers OT |

---

## 6. Success criteria

1. Operator can follow guide + skill and set up Chrome flag + inspector in &lt;15 minutes.
2. Clear **host MCP** vs **WebMCP** distinction in at least two docs.
3. Snippets show feature-detect + fallback when API absent.
4. All surfaces labeled **beta / experimental**.
5. No change to default session-start envelope or MCP policy.

## Related

- Operator guide: [docs/guides/webmcp-beta.md](../guides/webmcp-beta.md)
- Skill: `.grok/skills/webmcp-beta/SKILL.md`
- Host MCP: [multi-platform-mcp-and-host-tools.md](../guides/multi-platform-mcp-and-host-tools.md)
