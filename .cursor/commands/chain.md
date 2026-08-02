# /chain

Run an orchestrator **chain** by id (same as Grok and Claude).

**Default session opener:**

```text
/chain session-start
```

Other common ids: `eod-shutdown`, `session-end`, `delivery`, `always-on-memory`, `code-review`.

1. Read `CHAIN.md` or `chains/registry.yaml` for the chain id.
2. Follow `.cursor` rules + project cache (manifest-first).
3. Execute chain steps cache-first; cite cache files used.

User focus: the chain id or intent (e.g. `session-start`).
