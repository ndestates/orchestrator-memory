---
name: always-on-memory
description: "Always-on memory agent: ingest/consolidate/query via project model-route catalog + all agents; SQLite store; inbox watch; session brief."
argument-hint: "status|query <q>|ingest <text>|serve|models|agents|seed — e.g. 'query what is open'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - bash
  - read_file
---
# Always-On Memory

**Pattern:** [Google always-on-memory-agent](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/agents/always-on-memory-agent)  
**Product:** orchestrator **2.0.0+**

## Where it lives

| What | Path |
|------|------|
| CLI / daemon | `scripts/memory_agent.py` |
| Session brief | `scripts/session-memory-brief.py` |
| Engine | `scripts/_engine/memory_{store,models,agents,llm}.py` |
| **Runtime DB** | `reports/memory/memory.db` (gitignored) |
| Inbox | `reports/memory/inbox/` |
| Skill | `.github/skills/always-on-memory/SKILL.md` |
| Guide | `docs/guides/always-on-memory.md` |
| Tests | `tests/test_memory_agent.py` |
| Chain | `always-on-memory` + session-start `memory-brief` |

**Models:** full `scripts/model-route/catalog.yaml` (all OSS + free_cloud + host frontiers)  
**Agents:** full project roster (registry + `.grok` / `.claude` agents)

## Ops

| Verb | Command |
|------|---------|
| status | `python3 scripts/memory_agent.py status` |
| models | `python3 scripts/memory_agent.py models` |
| agents | `python3 scripts/memory_agent.py agents` |
| seed | `python3 scripts/memory_agent.py seed-situation` |
| ingest | `python3 scripts/memory_agent.py ingest --text "..." --source s` |
| query | `python3 scripts/memory_agent.py query "…"` |
| consolidate | `python3 scripts/memory_agent.py consolidate` |
| serve | `python3 scripts/memory_agent.py serve --port 8888` |
| brief | `python3 scripts/session-memory-brief.py` (auto-seed if empty or VERSION mismatch; `--seed` / `--no-seed`) |

Drop files in `reports/memory/inbox/` when `serve`/`watch` is running.

## Rules

- Never silent-switch host models; daemon uses Ollama when ready else heuristic.
- High-demand / security queries route to frontier host agents + security specialists.
- Scrub secrets via untrusted_text; dual-write vault lessons on ingest/consolidate.
- Session-start: run `session-memory-brief.py` after vault brief — auto-seed when the store is empty or `VERSION=` in memories is behind the file `VERSION`. Memory is SSOT for situation when seeded.
- **Stronger with every update:** ingest security find/triage/fix/apply lessons so
  closed vulns are not re-planned (see `SECURITY.md` + `docs/reference/stronger-with-every-update.md`).

## Related

- `/model-route` · vault · llm-wiki · session-start  
- Guide: `docs/guides/always-on-memory.md`
