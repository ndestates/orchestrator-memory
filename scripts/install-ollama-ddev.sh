#!/usr/bin/env bash
# Install Ollama as a DDEV add-on service (tyler36/ddev-ollama).
#
# Usage:
#   bash scripts/install-ollama-ddev.sh
#   bash scripts/install-ollama-ddev.sh --check-only
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CHECK_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only) CHECK_ONLY=1; shift ;;
    -h|--help)
      sed -n '2,7p' "$0" >&2
      exit 0
      ;;
    *) printf "[install-ollama-ddev] ERROR: unknown option: %s\n" "$1" >&2; exit 2 ;;
  esac
done

info() { printf "[install-ollama-ddev] %s\n" "$1"; }

if [[ ! -f .ddev/config.yaml ]]; then
  printf "[install-ollama-ddev] ERROR: no .ddev/config.yaml — initialize DDEV first\n" >&2
  exit 1
fi

if ! command -v ddev >/dev/null 2>&1; then
  printf "[install-ollama-ddev] ERROR: ddev not on PATH — install DDEV first\n" >&2
  exit 1
fi

if [[ -f .ddev/docker-compose.ollama.yaml ]] || [[ -f .ddev/commands/web/ollama ]]; then
  info "DDEV Ollama add-on already present"
  ddev restart
  info "Verify: ddev ollama list  (or: bash scripts/detect-ollama.sh)"
  exit 0
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  info "DDEV Ollama add-on not installed (check-only)"
  exit 1
fi

info "Installing tyler36/ddev-ollama add-on"
ddev add-on get tyler36/ddev-ollama
ddev restart

info "DDEV Ollama ready"
info "In web container: OLLAMA_HOST=http://ollama:11434"
info "Host agents: OLLAMA_HOST=http://127.0.0.1:11434 (see ddev describe)"
info "Pull a model: ddev ollama run llama3.2"
info "GPU (Linux/WSL2): cp scripts/ollama/ddev-compose.ollama-gpu.yaml.example .ddev/docker-compose.ollama-gpu.yaml && ddev restart"
info "Docs: docs/guides/local-ollama.md"