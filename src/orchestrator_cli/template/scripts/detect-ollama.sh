#!/usr/bin/env bash
# Local Ollama detection for orchestrator template and app repos.
#
# Reads runtime.local_llm from project manifest (none | ollama), checks CLI + API.
# Usage: bash scripts/detect-ollama.sh [--json]
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

JSON=0
[[ "${1:-}" == "--json" ]] && JSON=1

py=""
if command -v python3 >/dev/null 2>&1; then
  py=python3
elif command -v python >/dev/null 2>&1; then
  py=python
else
  printf "detect-ollama: ERROR: Python 3 required\n" >&2
  exit 1
fi

args=(scripts/ollama_detect.py --root "$ROOT")
[[ "$JSON" -eq 1 ]] && args+=(--json)

exec "$py" "${args[@]}"