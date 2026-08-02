# Multi-workstream session v2 + agent graphs — plan

**Date:** 2026-07-22 (updated)  
**Branch:** `feature/multi-workstream-session-v2-2026-07-22`  
**Status:** **Active** — plan updated from graph-engineering share ([@0xCodez 14-step graph roadmap](https://x.com/0xCodez/status/2079165300625330317); Grok share discuss: how this maps to Grok Build / multi-platform)  
**Version base:** 1.8.9  
**WebMCP:** **Not required.** Separate beta product. May appear as a *parked* registry row only if you track it — multi-workstream does not depend on it.

> Internal plan. Not for public docs site / npm packages.  
> License track remains **HELD READY** on `feature/opensource-apache-patreon-2026-07-22`.

---

## 0. One-sentence thesis

A **prompt** is a sentence; a **loop** is a cycle; a **harness** is the floor — but the **shape of the work** (what runs before what, what can run together, what must wait) is a **graph**.  
Orchestrator already has graph pieces (Shape B lanes, vault hash-chain, loop verifier, chains). Multi-stream v2 makes **day-scale workstreams** first-class nodes, and teaches **diamond graphs** (fan-out → reduce → synthesize) without multi-session SDK bloat.

---

## 1. Source map (14 steps → this repo)

| # | Graph principle | Orchestrator mapping |
|---|-----------------|----------------------|
| 01 | Nodes = jobs; edges = data flow | Workstream record / lane / vault event = node; `parents` / `contract_outputs` / handoff ≤80 tok = edge |
| 02 | Linear chain is a degenerate graph | Single-lane Shape A chains; redraw with Shape B when no data edge |
| 03 | Every node has a contract | `contract_outputs`, JSON schemas, license validate shape, MCP tool schemas |
| 04 | Edge is a data contract | Handoff blobs, vault parent hashes, chain step `handoff:` fields — prefer **code reduce** over agent chat |
| 05 | Fan-out with parallel | Shape B lanes `depends_on: []`; subagent parallel; future `workstream fanout` |
| 06 | Fan-in at a barrier | `merge_gates[]` / `contract_check`; vault synthesis node |
| 07 | Diamond: split → work → merge | **Canonical demo** (this branch): fan-out workstreams → code reduce → mermaid/JSON synthesize |
| 08 | Runtime conditional route | Branch on resume_first / dirty tree / tier; router node later |
| 09 | Verifier on the edge | `loop-verifier`, CSE session sweep, bug-hunter, adversarial verify pattern |
| 10 | Isolate failure | Worktree isolation for parallel writers; parallel() null-filter spirit; no shared dirty tree |
| 11 | Cycles that converge | Loop-until-dry (loop-triage + compound); dedupe against *all seen* vault ids |
| 12 | Tier models across nodes | Fan-out cheap; merge/judgment expensive; manifest token_policy lean |
| 13 | Topology = cost/latency | Prefer pipeline over barrier; barriers only when cross-set needed |
| 14 | Self-routing graphs | Orchestrator plans Shape B; saved chains in `chains/registry.yaml`; workflows as versioned scripts |

**Explicit non-port:** Claude Code “dynamic workflow JS” is inspiration, not a dependency. We implement with **Python scripts + git + existing chains/agents**.

---

## 2. Two layers (do not conflate)

| Layer | Lifetime | Parallelism | Example |
|-------|----------|-------------|---------|
| **Workstream** (day/week) | Days–weeks | Serial *focus*, parallel *tracking* | any named track (license, freemium, this feature, …) |
| **Agent graph** (one run) | Minutes | Concurrent nodes | Diamond over vault + workstream fan-out |

Multi-session Copilot SDK (mailchimp) stays **out** — N full chats each loading cache is the anti-pattern in `context-window-literacy.md`.

---

## 3. Workstream registry (locked: option B)

**Path:** `reports/sessions/workstreams.yaml`  
**CLI:** `python3 scripts/workstream.py {list|focus|hold|note|graph}`

| Field | Purpose |
|-------|---------|
| `id` | Stable key |
| `status` | `active` \| `held_ready` \| `parked` \| `held` \| `done` |
| `branch` | Git branch for focus/checkout when clean |
| `artifacts` | Plan/docs paths |
| `open` / `next` | Lean operator lines |
| `updated` | ISO date |

**Session-start (Phase 2):** print ≤5 `ws:` lines (~150 tokens). Do not dump artifacts.

**Focus policy:** `focus <id> --apply` checks out branch when tree clean (same spirit as remote_last). Held streams never auto-unhold.

---

## 4. Active multi-stream set (this branch)

| id | status | branch / note |
|----|--------|----------------|
| `multi-stream-graphs` | **active** | This branch — multi-stream tooling itself |
| `opensource-license` | **held_ready** | Apache + Pro EULA (paused) |
| `freemium-paypal` | **held** | Explicit unhold only |
| `webmcp-beta` | **parked** (optional) | Separate product — not multi-stream |

---

## 5. Graph example (what we can do *here*)

### 5.1 Diamond over workstreams + vault

```
                    [split: load registry + vault tip]
                   /        |         \
           [ws: A]      [ws: B]    [ws: C held…]
                   \        |         /
                    [reduce: code — no model]
                              |
                    [synthesize: mermaid + JSON report]
```

**Runnable (slash):**

```text
/multi-workstream list
/multi-workstream example
```

→ `reports/examples/agent-graphs/latest.md` · `latest.json`

### 5.2 Other graphs already in the product

| Graph | Where | Use |
|-------|--------|-----|
| **Vault integrity graph** | `reports/vault/events.jsonl` (`parents` edges) | Compound learning, tamper detection, precedents |
| **Shape B multi-lane** | `/orchestrator` | Parallel domain work with merge gates |
| **Loop diamond** | loop-triage → verifier → compound | L1 report-only + human gate |
| **Chain DAG** | `chains/registry.yaml` steps | Shared cache, ordered/optional steps |

### 5.3 Six “build this week” ideas (adapted)

1. **Security sweep fan-out** — one node per allowlisted surface; verifier before report (CSE + session-sweep pattern).  
2. **Cited research** — parallel source fetch → code dedupe → adversarial verify → synthesize memo.  
3. **Port/module file fan-out** — worktree isolation per file + test gate.  
4. **Diff adversarial review** — route on diff size; multi-lens reviewers.  
5. **Scheduled ecosystem scan** — saved chain, barrier rank, digest.  
6. **Unknown-size discovery** — loop-until-dry + vault dedupe of all seen finding ids.

---

## 6. Implementation phases

### Phase 0 — Plan ✅

- [x] Un-shelve multi-stream; license HELD READY  
- [x] Ingest graph 14-step map  
- [x] Decouple WebMCP (parked optional track only)  

### Phase 1 — CLI + diamond example (this slice)

- [x] `scripts/workstream.py`  
- [x] `scripts/workstream_graph_example.py` (workstreams + vault only)  
- [x] Docs under `docs/examples/agent-graphs/`  
- [x] Registry = operator tracks (primary multi-stream-graphs)  

### Phase 2 — Session-start lean block + multi-platform ✅

- [x] Envelope: `ws primary=… active=N held=N parked=N show=…` (max 5)  
- [x] `workstream.py brief` + `load_brief()`  
- [x] Platform procedures: `.grok` · `.claude` · `.github`/`.copilot` · `.gemini` · `.cursor` · `.chatgpt`  
- [x] Link from `docs/guides/daily-workflow.md`  
- [x] Session-context-envelope pointers mention `ws` on each surface  

### Phase 3 — Optional polish

- [x] Chain `workstream-graph-demo` (2026-07-25) — inventory diamond; alias `multi-workstream-demo`; optional `graph-example` step on `/chain multi-workstream` when asked  
- [ ] Vault event type `workstream_pointer` (only if useful)  
- [ ] EOD auto-update active `next` from resume card  

---

## 7. Success criteria

| Criterion | Measure |
|-----------|---------|
| Clear plan | This doc + day TODO point here |
| Multi-stream real | `/multi-workstream list` shows active + held tracks you care about |
| Graph demo | Diamond over **workstreams + vault** only (no product demos) |
| Token safe | No N full cache loads; handoffs lean |
| License held | No Apache/EULA expansion without unhold |
| Git discipline | Commits after each slice; secrets guard |

---

## 8. Operator defaults (locked unless you change them)

1. Registry path **B** — `reports/sessions/workstreams.yaml`  
2. `focus --apply` auto-checkout when **clean** — **yes**  
3. Held streams do **not** block remote_last — **yes**  
4. Max workstreams at session-start — **5**  

---

## 9. Document history

| Date | Change |
|------|--------|
| 2026-07-22 | Initial multi-workstream v2 |
| 2026-07-22 | **Update:** 14-step agent-graph map; WebMCP merge; diamond example; CLI; multi-stream registry |
| 2026-07-22 | **Phase 2:** envelope `ws` line; multi-platform skills/prompts (ChatGPT·Claude·Copilot·Cursor·Gemini·Grok) |
