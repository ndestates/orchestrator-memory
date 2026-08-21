# Local Ollama (optional BYOM)

[UPDATED 2026-07-14] — restored optional multi-runtime install for v1.8.1

Use **Ollama** as an optional bring-your-own-model (BYOM) path for local inference. Cloud AI subscriptions (Grok, Copilot, Claude, etc.) are **not** included with the orchestrator license — Ollama is a separate, operator-managed runtime.

**Free-model routing:** for low-tier tasks Orchestrator may offer open-source Ollama models first — see [model-route-free-oss.md](model-route-free-oss.md) and `/model-route`.

The template ships **detect** and **install** scripts for three local runtimes:

| Runtime | Best for | Install |
|---------|----------|---------|
| **Host** | Orchestrator template, Windows, no containers | `install-ollama.sh` / `install-ollama.ps1` |
| **DDEV** | Laravel / PHP app repos with `.ddev/` | `install-ollama-ddev.sh` (add-on service) |
| **Docker Compose** | Pure Docker local stacks (no DDEV) | `install-ollama-compose.sh` (compose overlay) |

## Manifest

Edit `.github/project-manifest.yaml` (canonical), then sync:

```bash
python3 scripts/sync_manifests.py
```

```yaml
runtime:
  environment_manager: "ddev"          # ddev | docker-compose | local
  local_llm: "ollama"                 # none | ollama
  ollama_runtime: "auto"              # auto | host | ddev | docker-compose
```

| Field | Behavior |
|-------|----------|
| `local_llm` | `none` (default) or enable Ollama expectations |
| `ollama_runtime` | `auto` picks from `environment_manager` + `.ddev/` / compose files |
| `environment_manager` | Primary signal when `ollama_runtime: auto` |

## Install (auto-detect)

`install-ollama.sh` reads the manifest and project files, then routes to the right path:

```bash
bash scripts/install-ollama.sh                 # auto
bash scripts/install-ollama.sh --target ddev   # force DDEV add-on
bash scripts/install-ollama.sh --target docker-compose
bash scripts/install-ollama.sh --target host
bash scripts/install-ollama.sh --check-only
```

During bootstrap:

```bash
bash scripts/install.sh --ollama    # same auto-routing
```

Windows host-only (no DDEV in PowerShell):

```powershell
.\scripts\install.ps1 -Ollama
.\scripts\install-ollama.ps1
```

### DDEV app repos

Requires an existing `.ddev/config.yaml`:

```bash
bash scripts/install-ollama-ddev.sh
# equivalent: ddev add-on get tyler36/ddev-ollama && ddev restart
```

- **Inside web container:** `OLLAMA_HOST=http://ollama:11434`
- **Host agents (Grok):** `OLLAMA_HOST=http://127.0.0.1:11434`
- **Commands:** `ddev ollama list`, `ddev ollama run llama3.2`
- **GPU (Linux/WSL2):** copy `scripts/ollama/ddev-compose.ollama-gpu.yaml.example` → `.ddev/docker-compose.ollama-gpu.yaml`, then `ddev restart`

### Pure Docker Compose (not DDEV)

For projects using `docker-compose.yml` / `compose.yaml` without DDEV:

```bash
bash scripts/install-ollama-compose.sh
```

This copies `scripts/ollama/docker-compose.ollama.yaml` → `docker-compose.ollama.yaml` and runs:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yaml up -d ollama
```

- **Sibling containers:** `OLLAMA_HOST=http://ollama:11434`
- **Host agents:** `OLLAMA_HOST=http://127.0.0.1:11434` (published port)
- **Pull model:** `docker compose exec ollama ollama pull llama3.2`

Commit `docker-compose.ollama.yaml` (and the GPU snippet if used) to version control.

### Host (template / Windows)

Official Ollama installer on the machine:

```bash
bash scripts/install-ollama.sh --target host
```

## Detect at session start

`/chain session-start` runs detection when Ollama is configured or present:

```bash
bash scripts/detect-ollama.sh
bash scripts/detect-ollama.sh --json
```

| Output | Meaning |
|--------|---------|
| `ollama_runtime` | Resolved target: `host`, `ddev`, or `docker-compose` |
| `ollama_service_configured` | `yes` when add-on / compose overlay is present |
| `ollama_host_internal` | URL for in-container clients (`http://ollama:11434`) |
| `ollama_host_external` | URL for host agents (`http://127.0.0.1:11434`) |
| `local_llm_ready` | `yes` when manifest expects Ollama and API is up |
| `ollama_note` | Install or start hint |

## Environment

| Variable | Default | Used by |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Host-side agents and apps |

Inside DDEV web or compose app containers, prefer `http://ollama:11434` in app `.env`.

## Troubleshooting

### DDEV: `local_llm_ready=no`

1. `bash scripts/install-ollama-ddev.sh`
2. `ddev start && ddev restart`
3. `ddev ollama list`

### Compose: service not running

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yaml up -d ollama
docker compose ps ollama
```

### Host agents cannot reach in-container Ollama

Use the **external** URL (`127.0.0.1:11434`), not `ollama:11434` — that hostname only resolves inside the Docker network.

### WSL + Windows Ollama

Set `OLLAMA_HOST` to the Windows host gateway IP if Ollama runs on Windows and agents run in WSL.

## Licensing reminder

- **Orchestrator license** — required for third-party `init` / `upgrade` when a license URL is configured.
- **Ollama + models** — your hardware and downloads; not bundled by ND Estates.
- **Cloud AI** — separate subscriptions; see `orchestrator license` BYOM line.

## Related

- [Installation](installation.md)
- [Daily workflow](daily-workflow.md)
- [Template adoption](../TEMPLATE_ADOPTION.md)