# Agent graphs — examples

Concrete **graph** demos for this repo (nodes / edges / diamond), not linear “do A then B” chats.

## Workstream diamond (runnable)

**Operators (Grok / Claude / etc.):**

```text
/multi-workstream list
/multi-workstream graph
/multi-workstream example
```

or:

```text
/chain workstream-graph-demo
/chain multi-workstream-demo
```

(`/chain multi-workstream` also has an **optional** `graph-example` step — runs only when you ask for the demo.)

**Agents / CI (implementation):**

```bash
python3 scripts/workstream.py list
python3 scripts/workstream.py graph
python3 scripts/workstream_graph_example.py
```

Outputs:

- `reports/examples/agent-graphs/latest.md` — mermaid + node table  
- `reports/examples/agent-graphs/latest.json` — machine-readable contracts  

Plan: `docs/internal/MULTI-WORKSTREAM-SESSION-V2-PLAN.md`  
**Operator guides (per LLM):** [docs/guides/multi-workstream.md](../../guides/multi-workstream.md)  
Source inspiration: graph engineering (nodes, edges, fan-out, fan-in, verifier, isolation).

## Other graphs in-product

| Graph | Entry |
|-------|--------|
| Vault hash-chain | `reports/vault/events.jsonl`, `scripts/session-vault-brief.py` |
| Shape B multi-lane | `/orchestrator` multi-lane plan |
| Loop triage → verify → compound | `/loop-triage`, `/loop-verifier`, `/loop-compound` |
| WebMCP beta tools | `/webmcp-beta` skill, `docs/guides/webmcp-beta.md` |
