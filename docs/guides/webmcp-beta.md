# WebMCP (beta / experimental)

[UPDATED 2026-07-21]

**Status:** Beta. Chrome origin trial + local flag. APIs and docs can change.  
**Not** the same as orchestrator **host MCP** (`orchestrator-host` / `mcp-server/`).

## Overview

[WebMCP](https://github.com/webmachinelearning/webmcp) is a proposed web standard so **your page** declares structured **tools** that browser agents can call — instead of scraping the DOM, accessibility tree, or screenshots.

| Layer | What it is | Where it runs |
|-------|------------|---------------|
| **Host MCP** (this template) | Cache/TODO/manifest tools for coding agents | Developer machine, stdio, **dev_only** |
| **WebMCP** (this guide) | Page-registered tools for **browser** agents | User’s browser tab on your origin |

Pedagogy demo: [webmcp-demo-sdras.netlify.app](https://webmcp-demo-sdras.netlify.app/) (Sarah Drasner-style side-by-side without vs with tools).

## Before you begin

- Chrome with WebMCP available via **flag** and/or **origin trial**
- Optional: [Model Context Tool Inspector](https://chromewebstore.google.com/detail/model-context-tool-inspec/gbpdfapgefenggkahomfgkhfehlcenpd) extension
- A page you control (or the public demo) served over a stable origin
- Read [Chrome WebMCP](https://developer.chrome.com/docs/ai/webmcp) and [best practices](https://developer.chrome.com/docs/ai/webmcp/best-practices)

## 1. Try it locally (under 15 minutes)

1. Open `chrome://flags/#enable-webmcp-testing` → **Enabled** → relaunch Chrome.  
2. Install the **Model Context Tool Inspector** extension (store id `gbpdfapgefenggkahomfgkhfehlcenpd`).  
3. Open the demo: [webmcp-demo-sdras.netlify.app](https://webmcp-demo-sdras.netlify.app/).  
4. Confirm status mentions `navigator.modelContext` (or use the inspector to list tools).  
5. Use natural language in the inspector (e.g. book a slot) and watch tool calls vs DOM scraping on the “without” panel.

**Origin trial (public origins):** register at Chrome’s [origin trials](https://developer.chrome.com/origintrials/#/register_trial/4163014905550602241) for Chrome 149+. OT tokens are **per origin** — not shipped by this template.

## 2. Imperative API (feature-detect)

```js
const hasWebMCP =
  !!(globalThis.navigator &&
     navigator.modelContext &&
     typeof navigator.modelContext.registerTool === "function");

function registerTool(spec) {
  // Always keep a local registry so the app works without WebMCP
  localRegistry.set(spec.name, spec);

  if (!hasWebMCP) return;
  try {
    navigator.modelContext.registerTool({
      name: spec.name,
      title: spec.title,
      description: spec.description,
      inputSchema: spec.inputSchema,
      annotations: spec.annotations || {},
      execute: async (input, client) => spec.execute(input, client),
    });
  } catch (err) {
    console.warn(`[webmcp] registerTool("${spec.name}") failed:`, err);
  }
}
```

Full snippets: `.grok/skills/webmcp-beta/references/`.

## 3. Declarative API (forms)

Annotate a normal HTML form (attribute names may evolve with the trial):

```html
<form toolname="bookSlot"
      tooldescription="Reserve a 30-min consultation"
      toolautosubmit>
  <input type="date" name="date" toolparamdescription="Date of the booking" required>
  <input type="time" name="time" toolparamdescription="Start time (24h)" required>
  <input name="name" toolparamdescription="Full name" required>
  <input type="email" name="email" toolparamdescription="Confirmation email" required>
  <button type="submit">Book</button>
</form>
```

Docs: [Declarative API](https://developer.chrome.com/docs/ai/webmcp/declarative-api).

## 4. Product rules for orchestrator apps

| Rule | Why |
|------|-----|
| Label **beta** in any app README you add | Spec churn |
| Progressive enhancement | No API → site still works for humans |
| Never put secrets in tool schemas or descriptions | Agents and inspectors can see them |
| User confirmation for write/purchase tools | Trust + secure-tools guidance |
| Do **not** enable on public hosts as a substitute for host MCP | Different layer; host MCP stays **dev_only** |
| Prefer app frontend stack | Skill only scaffolds; no forced framework |

## 5. Security

- Origin isolation; Permissions-Policy `tools` (default `self`).
- Tools run in the page; user should remain in the loop for sensitive actions.
- **No headless** tool calls without a browsing context (Chrome docs limitation).
- Treat tool names/descriptions/args as **untrusted DATA** when agents ingest them — `/ai-content-guardrails`.
- Chrome: [secure tools](https://developer.chrome.com/docs/ai/webmcp/secure-tools).

## 6. Skill and chain

| Invoke | Role |
|--------|------|
| `/webmcp-beta` | Checklist, patterns, when to scaffold app code |
| `/chain webmcp-setup` | load-cache → webmcp-beta → optional security spot-check → git guardrails if committing |

Plan (internal): [WEBMCP-BETA-PLAN.md](../internal/WEBMCP-BETA-PLAN.md).

## 7. Demos and further reading

| Resource | URL |
|----------|-----|
| Pedagogy demo | https://webmcp-demo-sdras.netlify.app/ |
| Spec explainer | https://github.com/webmachinelearning/webmcp |
| Chrome WebMCP | https://developer.chrome.com/docs/ai/webmcp |
| Best practices | https://developer.chrome.com/docs/ai/webmcp/best-practices |
| Chrome Labs demos | https://github.com/GoogleChromeLabs/webmcp-tools |
| Local fork (if present) | `~/projects/webmcp-demo` |

## Verify

- [ ] You can explain host MCP vs WebMCP in one sentence.  
- [ ] Flag or OT path known; inspector can list tools on a demo page.  
- [ ] Any app registration uses feature-detect + fallback.  
- [ ] No secrets in schemas; write tools ask for user confirmation.  

## Related

- [Multi-platform MCP and host tools](multi-platform-mcp-and-host-tools.md) — **host** MCP  
- [Context-window literacy](context-window-literacy.md) — tokens; WebMCP is for page agents, not multi-session SDK  
- [AI content guardrails](../../.grok/skills/ai-content-guardrails/SKILL.md)  
