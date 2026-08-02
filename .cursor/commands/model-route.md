# /model-route

> Suggest free open-source LLMs (Ollama) when the task does not need the current frontier model; offer stay | oss | install-oss | free-cloud. Never silent-switch.

**Platform:** Cursor · same skill as Grok `/model-route` · Claude `/model-route`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `[--task …] [--chain-id …] [--platform grok|claude|cursor|gemini|copilot]`

# Model route — free / open-source first

**Open-source first.** Prefer local Ollama OSS models for low-tier work. Cloud free
tiers are secondary. Never auto-switch the host model — offer and wait.

## Run

```bash
python3 scripts/model-route-suggest.py --task "<user ask>" --chain-id <id> --platform grok
# JSON:
python3 scripts/model-route-suggest.py --task "…" --json
```

Catalog (must include `license: open_weights` models):
`scripts/model-route/catalog.yaml`

## When to offer

| Demand | Behavior |
|--------|----------|
| **low** | Offer OSS if ready; else `install-oss` + free-cloud |
| **medium** | Offer OSS only if installed; else stay |
| **high** / security chains | **stay** — no free nag |

## Operator replies

- `stay` — continue on current frontier/host model  
- `oss` — switch session/model picker to the named Ollama tag  
- `install-oss` — `bash scripts/install-ollama.sh` then `ollama pull <tag>`  
- `free-cloud` — host free tier (not open weights); see catalog  

## Wire-in

- `/chain` Phase 1 when `token_tier: low`  
- session-start tone / after CTX (once per session)  
- Guide: `docs/guides/model-route-free-oss.md`  
- Ollama: `docs/guides/local-ollama.md`

## Suppress

`ORCHESTRATOR_MODEL_ROUTE_OFFER=0`

User focus (optional): use any extra chat text as $ARGUMENTS.
