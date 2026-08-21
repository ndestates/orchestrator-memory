# Multi-workstream — shared implementation (all LLMs)

[UPDATED 2026-07-22]

**Single contract for every host.** Surfaces only change *which directory is primary*; slash commands, agent map, scripts, chains, and rules are identical.

**What multi-workstream is for:** tracking and switching among **your** work items (features, holds, PRs) in one chat.  
**What it is not:** a product demo (WebMCP, etc.). Optional parked tracks may exist; they are not required to use multi-stream.

Scripts are the **runtime**. Slash commands are the **operator UX**. Agents translate slash → scripts; they do **not** tell operators to type `python3 scripts/…` as the primary interface.

---

## 1. Operator slash commands (same on every model)

| Operator types | Meaning |
|----------------|---------|
| `/chain session-start` | Spin-up; compact CTX includes **`ws primary=… active=N held=N show=…`** |
| `/multi-workstream` | Same as `list` |
| `/multi-workstream list` | Full workstream table |
| `/multi-workstream brief` | One-line summary (CTX shape) |
| `/multi-workstream graph` | Mermaid of registry focus topology |
| `/multi-workstream focus <sel>` | Set primary (single: `1` or slug) |
| `/multi-workstream focus <sel> --apply` | Primary + checkout when clean |
| `/multi-workstream hold <sel>` | status → `held` (`1`, `1,2`, `all`) |
| `/multi-workstream hold <sel> --ready` | status → `held_ready` |
| `/multi-workstream activate <sel>` | status → `active` — **`all`** or `1,2,3` or `1-3` |
| `/multi-workstream unhold <sel>` | Alias of `activate` |
| `/multi-workstream park <sel>` | status → `parked` |
| `/multi-workstream add <slug> …` | Register new track (slug only, not a number) |
| `/multi-workstream note <sel> --next "…"` | Update next (single selector) |

**Selectors:** `1` · `2,3` · `1-3` · `all` · or slug id. Numbers are **1-based list order** from `/multi-workstream list`.
| `/multi-workstream example` | Inventory diamond (registry + vault mermaid probe) |
| `/multi-workstream diamond` | **Shape B recommendation** — what can safely multi-lane (no auto-exec) |
| `/multi-workstream recommend` | Alias of `diamond` |
| `/multi-workstream demo` | Alias of `example` |
| `/chain multi-workstream` | list + brief + graph (+ optional graph-example if asked) |
| `/chain multi-workstream-diamond` | Session-friendly: run `diamond` recommend |
| `/chain multi-workstream-demo` | Alias path for inventory example |
| `/chain workstream-graph-demo` | Plan name — same inventory example as multi-workstream-demo |
| `/multi-workstream serial` | **Alternative to diamond** — primary only, no parallel plan |
| `/multi-workstream guard` | Integrity check (no merge; on-course safeguards) |
| `/multi-workstream prompts` | **What is going on** — merge-ready / open PR / WIP / frozen + recommendations |
| `/multi-workstream ready` | Alias of `prompts` |
| `/multi-workstream status` | Alias of `prompts` |
| `/multi-workstream worktree list\|add\|remove\|status` | Git worktree isolation |

Natural language that means the same thing (e.g. “list workstreams”, “run diamond demo”) **must** map to the same rows above.

---

## 2. Agent execution map (required — identical)

Parse slash arguments / user intent. Run **exactly** one path via bash:

| Args | Shell (agent only) |
|------|---------------------|
| *(empty)* / `list` | `python3 scripts/workstream.py list` |
| `brief` | `python3 scripts/workstream.py brief` |
| `graph` | `python3 scripts/workstream.py graph` |
| `focus ID` | `python3 scripts/workstream.py focus ID` |
| `focus ID --apply` | `python3 scripts/workstream.py focus ID --apply` |
| `hold ID` | `python3 scripts/workstream.py hold ID` |
| `hold ID --ready` | `python3 scripts/workstream.py hold ID --ready` |
| `activate ID` / `unhold ID` | `python3 scripts/workstream.py activate ID` |
| `park ID` | `python3 scripts/workstream.py park ID` |
| `add ID …` | `python3 scripts/workstream.py add ID …` |
| `note ID --next …` | `python3 scripts/workstream.py note ID --next "…"` |
| `note ID --open …` | `python3 scripts/workstream.py note ID --open "…"` |
| `example` / `demo` | `python3 scripts/workstream_graph_example.py` then summarize `reports/examples/agent-graphs/latest.json` **reduce** block |
| `diamond` / `recommend` / `shape-b` / `shapeb` | `python3 scripts/workstream_recommend.py` then print compact + path to `recommend-latest.md` |
| `serial` | print primary-only plan (no parallel) |
| `guard` | `python3 scripts/workstream_guard.py` |
| `prompts` / `ready` / `status` | `python3 scripts/workstream_prompts.py` |
| `worktree …` | `scripts/workstream_worktree.py` via workstream.py |

After running, print the **command output**. Prefer framing as:

> Ran `/multi-workstream list` → …

Never: “Please run `python3 scripts/workstream.py list` yourself” as the primary instruction.

---

## 3. Shared runtime files (same for all hosts)

| Path | Role |
|------|------|
| `reports/sessions/workstreams.yaml` | Registry (source of truth) |
| `scripts/workstream.py` | list / brief / graph / focus / hold / note |
| `scripts/workstream_graph_example.py` | Inventory diamond (workstreams + vault) |
| `scripts/workstream_recommend.py` | Shape B safe multi-lane **recommendation** (no auto-exec) |
| `scripts/session-context-envelope.py` | Session-start; emits `ws` line |
| `reports/examples/agent-graphs/latest.md` | Inventory diamond report |
| `reports/examples/agent-graphs/recommend-latest.md` | Shape B recommendation report |
| `chains/registry.yaml` | `/multi-workstream`; chains `multi-workstream`, `multi-workstream-diamond`, `multi-workstream-demo`, `workstream-graph-demo` |

---

## 4. Session-start behaviour (same)

1. Operator: `/chain session-start`  
2. Agent runs envelope (implementation: `python3 scripts/session-context-envelope.py --write`)  
3. Print compact CTX **verbatim**, including:

```text
ws primary=… active=N held=N parked=N show=id1,id2,…
```

4. Max **5** ids in `show=`. Do not dump full YAML unless editing tracks.  
5. Surface resume card / `ask:` per envelope rules.  
6. **Optional one-command plan** (operator): `/multi-workstream diamond`  
   → Shape B recommendation: primary L0 + safe parallel lanes (docs/chore/minor) + blocked held items.  
   **Never auto-executes.** Never unholds. Preserves primary focus.

---

## 5. Status semantics (same)

| Status | Meaning |
|--------|---------|
| `active` | May work this track |
| `held_ready` | Paused, resume-ready; no expand until unhold |
| `held` | Hard hold (e.g. PayPal) |
| `parked` | Low priority |
| `done` | Closed |

---

## 6. Hard rules (same on every model)

1. **Primary surface only** for skill/command *procedure text* (see host banner). Shared OK: `TODO/`, `docs/`, `scripts/`, `reports/`, `chains/`.  
2. **One primary focus** at a time; many tracks **tracked** in parallel.  
3. **Never auto-unhold** license / PayPal / other held tracks.  
4. **No** multi-session Copilot SDK port from mailchimp.  
5. Graph **edges** prefer code reduce (diamond demo), not N full chat caches.  
6. `focus --apply` **blocks** if git tree dirty — commit/stash first.  
7. Slash-first replies; scripts are agent implementation.

---

## 7. Chains (same)

| Chain | Steps |
|-------|--------|
| `/chain multi-workstream` | skill args → list, then brief, then graph; optional `graph-example` when asked |
| `/chain multi-workstream-diamond` | skill args → **diamond recommend** (Shape B, no auto-exec) |
| `/chain multi-workstream-demo` | skill args → inventory `example` |
| `/chain workstream-graph-demo` | skill args → inventory `example` (plan name; alias of multi-workstream-demo) |

## 7b. Diamond recommendation rules (project-safe)

1. **Recommend only** — no subagent fan-out until operator says e.g. `approve parallel`.  
2. **Primary = L0** always; parallel lanes must not steal focus or checkout held branches.  
3. **Safe parallel** heuristics: docs, guides, changelog, tests, chore, wording, examples.  
4. **Blocked**: held/parked status; license/EULA/PayPal/production/secrets keywords.  
5. **Default serial** for implement/refactor/schema unless operator overrides.  
6. Cap parallel safe lanes (default 4). Merge gates listed in `recommend-latest.md`.

---

## 8. Platform surface map (path only differs)

| Host | Primary tree | Procedure entry |
|------|--------------|-----------------|
| Grok | `.grok/` | `.grok/skills/multi-workstream/SKILL.md` |
| Claude | `.claude/` | `.claude/commands/multi-workstream.md` |
| Copilot | `.github/` + `.copilot/` | `.github/skills/multi-workstream/SKILL.md` · `.copilot/skills/multi-workstream/SKILL.md` |
| ChatGPT | `.chatgpt/` | `.chatgpt/prompts/multi-workstream.md` |
| Gemini | `.gemini/` | `.gemini/prompts/multi-workstream.md` |
| Cursor | `.cursor/` | `.cursor/rules/multi-workstream.mdc` |

**Sync:** `python3 scripts/sync-multi-workstream-surfaces.py`  
**Guides hub:** `docs/guides/multi-workstream.md`  
**Per-host guide:** `docs/guides/multi-workstream/<host>.md` (same steps; banner only differs)
