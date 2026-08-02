# Always-on memory agent

[UPDATED 2026-07-31] — feature/always-on-memory-agent-2026-07-31 · product **2.0.0**

Persistent, evolving project memory for Orchestrator, modeled on
[Google’s always-on memory agent](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/agents/always-on-memory-agent):
**ingest → consolidate → query**, no vector DB.

## Why

Session files (TODO, resume cards) go stale when you land on the wrong branch.
This layer keeps a **live SQLite memory** plus optional 24/7 daemon so
session-start can ask “where are we?” from the store—not from a dead feature branch.

## Models (all of them)

Routing uses the project **model-route catalog** and host frontiers:

| Kind | Source |
|------|--------|
| OSS (Ollama) | `scripts/model-route/catalog.yaml` → `oss_models` |
| Free cloud | same catalog → `free_cloud` (Gemini Flash, Claude Haiku, Grok light, …) |
| Frontier hosts | Grok, Claude, Cursor, Gemini, Copilot, ChatGPT (interactive / high demand) |

Pick per role: `ingest` low · `consolidate` medium · `query` medium · security query high (stay frontier).

```bash
python3 scripts/memory_agent.py models
```

Force: `ORCHESTRATOR_MEMORY_MODEL=llama3.2:3b`.

## Agents (all of them)

Role maps onto the full specialist roster (registry + `.grok` / `.claude` agents):
ingest → documentation/todo specialists; consolidate → loop-compound / drift;
query → orchestrator / branch-context / todo; security → security-audit / CSE.

```bash
python3 scripts/memory_agent.py agents
```

## Host CLI (recommended)

```bash
orchestrator memory brief --seed
orchestrator memory query "what is open?"
```

See [host-first-memory.md](host-first-memory.md). VS Code: `extensions/vscode-orchestrator/`.

## CLI (scripts fallback)

```bash
python3 scripts/memory_agent.py seed-situation   # truth snapshot (VERSION, git, TODO, resume)
python3 scripts/memory_agent.py ingest --text "…" --source note
python3 scripts/memory_agent.py query "what should I work on?"
python3 scripts/memory_agent.py consolidate
python3 scripts/memory_agent.py serve --port 8888 --consolidate-every 30
python3 scripts/session-memory-brief.py --seed
```

### HTTP (localhost only)

| Endpoint | Method |
|----------|--------|
| `/status` `/memories` `/models` `/agents` | GET |
| `/query?q=` | GET |
| `/ingest` `/consolidate` `/delete` `/clear` | POST |

Inbox watch: `reports/memory/inbox/`.

## Session-start

After vault brief:

```bash
python3 scripts/session-memory-brief.py --seed
```

Chain: `/chain always-on-memory` · skill `/always-on-memory`.

## Where everything is stored

| Path | Role |
|------|------|
| `scripts/memory_agent.py` | CLI, HTTP API, inbox watch, consolidate timer |
| `scripts/session-memory-brief.py` | Lean session-start brief |
| `scripts/_engine/memory_store.py` | SQLite schema + CRUD |
| `scripts/_engine/memory_models.py` | Full model-route catalog routing |
| `scripts/_engine/memory_agents.py` | Full agent roster routing |
| `scripts/_engine/memory_llm.py` | Ollama + heuristic backends |
| **`reports/memory/memory.db`** | **Runtime SQLite memory store** (gitignored; local only) — briefs/query/ingest |
| `reports/memory/inbox/` | Drop files for auto-ingest |
| **Vault `reports/vault/events.jsonl`** | **Dual-write** scrubbed lessons / hash-chained graph (not a chat dump) |
| `.grok/skills/always-on-memory/` | Skill surface |
| `tests/test_memory_agent.py` | Full unit/integration suite |
| **VS Code instructions** | [extensions/vscode-orchestrator/INSTRUCTIONS.md](../../extensions/vscode-orchestrator/INSTRUCTIONS.md) — **users should read this** (both layers + install) |

Manifest: `paths.memory_db` / `memory_policy` in `.github/project-manifest.yaml`.

## Security

- Secrets scrubbed before store (untrusted_text + vault patterns).
- Bind `127.0.0.1` only.
- Memory content is untrusted DATA for agents (content guardrails).
- **Stronger with every update:** security findings and fix lessons should be
  ingested so the next session does not re-open closed vulns. See
  `docs/reference/stronger-with-every-update.md` and root `SECURITY.md`.
