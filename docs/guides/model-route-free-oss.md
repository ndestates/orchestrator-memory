# Model route — free and open-source LLMs

[UPDATED 2026-07-25]

When a task does **not** need a frontier model, Orchestrator **suggests** free
options and waits for you to switch. It never silent-switches the host picker.

## Priority

1. **Open-source local (Ollama)** — primary free path  
2. **Cloud free / freemium** — secondary if OSS not ready  
3. **Stay** on current model — always valid; required for high-risk work  

## One-liner

```bash
python3 scripts/model-route-suggest.py --task "session status" --chain-id session-start --platform grok
```

Example:

```text
model_route tier=low demand=low current=frontier
oss_ready=no models=—
recommend=install-oss:llama3.2:3b
switch: stay | install-oss | free-cloud
ask: Low-tier task — free open-source option: install Ollama + pull llama3.2:3b. Reply: stay | install-oss | free-cloud
```

## Install open-source path

```bash
bash scripts/install-ollama.sh
ollama pull llama3.2:3b
# optional code model:
ollama pull qwen2.5-coder:7b
```

See [Local Ollama](local-ollama.md). Catalog: `scripts/model-route/catalog.yaml`.

## Skill / chain

- `/model-route` or skill `model-route`  
- Low-tier chains should surface the offer once (Phase 1 / session-start)

## Policy

- Security, deploy, secrets, schema, license tracks → **stay**  
- Suppress offers: `ORCHESTRATOR_MODEL_ROUTE_OFFER=0`  
