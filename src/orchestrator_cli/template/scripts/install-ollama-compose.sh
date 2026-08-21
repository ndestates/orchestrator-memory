#!/usr/bin/env bash
# Install Ollama as a docker-compose service for pure Docker local stacks.
#
# Usage:
#   bash scripts/install-ollama-compose.sh
#   bash scripts/install-ollama-compose.sh --check-only
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
    *) printf "[install-ollama-compose] ERROR: unknown option: %s\n" "$1" >&2; exit 2 ;;
  esac
done

info() { printf "[install-ollama-compose] %s\n" "$1"; }

compose_file=""
for candidate in compose.yaml docker-compose.yml docker-compose.yaml; do
  if [[ -f "$candidate" ]]; then
    compose_file="$candidate"
    break
  fi
done

if [[ -z "$compose_file" ]]; then
  info "No base compose file — creating minimal docker-compose.yml"
  compose_file="docker-compose.yml"
  cat >"$compose_file" <<'EOF'
# Minimal base for local Docker stack (extend with your app services).
services: {}
EOF
fi

overlay="docker-compose.ollama.yaml"
snippet="scripts/ollama/docker-compose.ollama.yaml"

if [[ -f "$overlay" ]]; then
  info "Found $overlay"
elif [[ -f "$snippet" ]]; then
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    info "$overlay not deployed (check-only)"
    exit 1
  fi
  cp "$snippet" "$overlay"
  info "Copied $snippet → $overlay"
else
  printf "[install-ollama-compose] ERROR: missing $snippet\n" >&2
  exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  info "Compose Ollama overlay present (check-only)"
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  printf "[install-ollama-compose] ERROR: docker not on PATH\n" >&2
  exit 1
fi

info "Starting Ollama service"
docker compose -f "$compose_file" -f "$overlay" up -d ollama

info "Compose Ollama ready"
info "In compose network: OLLAMA_HOST=http://ollama:11434"
info "Host agents: OLLAMA_HOST=http://127.0.0.1:11434"
info "Pull a model: docker compose -f $compose_file -f $overlay exec ollama ollama pull llama3.2"
info "Docs: docs/guides/local-ollama.md"