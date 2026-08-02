#!/usr/bin/env bash
# MCP smoke: real stdio handshake — list_tools + health_check (no IDE).
#
# Usage:
#   bash scripts/mcp-smoke.sh              # JSON report, exit 0/1
#   bash scripts/mcp-smoke.sh --quiet      # one-line stderr, for session-start
#   bash scripts/mcp-smoke.sh --no-ensure  # skip ensure-mcp-host (CI after pip install)
#
# Exit: 0 = handshake OK · 1 = fail · 2 = blocked (no mcp-server / public env)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi
export PROJECT_ROOT="$ROOT"

QUIET=0
DO_ENSURE=1
for _arg in "$@"; do
  case "${_arg}" in
    --quiet|-q) QUIET=1 ;;
    --no-ensure) DO_ENSURE=0 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
  esac
done

if [[ ! -d "$ROOT/mcp-server" ]]; then
  echo "mcp-smoke: no mcp-server/ at $ROOT (skip)" >&2
  exit 2
fi

if [[ "${DO_ENSURE}" -eq 1 && -f "$ROOT/scripts/ensure-mcp-host.sh" ]]; then
  if ! bash "$ROOT/scripts/ensure-mcp-host.sh" --quiet 2>/dev/null; then
    # CI often has pip install -e without .venv — still try module path
    if [[ "${QUIET}" -eq 1 ]]; then
      echo "mcp-smoke: ensure-mcp-host failed; trying installed package" >&2
    fi
  fi
fi

# Prefer venv python that has the package; else python3 with PYTHONPATH
PY=""
if [[ -x "$ROOT/mcp-server/.venv/bin/python" ]]; then
  PY="$ROOT/mcp-server/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
  export PYTHONPATH="${ROOT}/mcp-server/src${PYTHONPATH:+:$PYTHONPATH}"
else
  echo "mcp-smoke: no python3" >&2
  exit 1
fi

SMOKE_ARGS=(--project-root "$ROOT")
if [[ "${QUIET}" -eq 1 ]]; then
  SMOKE_ARGS+=(--quiet)
fi

# shellcheck disable=SC2086
exec "$PY" -m orchestrator_mcp.smoke "${SMOKE_ARGS[@]}"
