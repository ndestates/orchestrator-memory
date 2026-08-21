#!/usr/bin/env bash
# Cursor / Grok / Claude Desktop MCP entrypoint — runs orchestrator-mcp inside DDEV web container.
# Host path: scripts/mcp-ddev-stdio.sh
# Requires: ddev started, mcp-server/ present in project root.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi
cd "$ROOT"

if ! command -v ddev >/dev/null 2>&1; then
  echo "ddev not found on PATH" >&2
  exit 1
fi

if [[ ! -d mcp-server/src/orchestrator_mcp ]]; then
  echo "mcp-server not installed in $ROOT" >&2
  exit 1
fi

DDEV_PROJECT=""
if ddev describe >/dev/null 2>&1; then
  :
elif [[ -f .ddev/config.yaml ]]; then
  DDEV_PROJECT="$(awk '/^name:/{print $2; exit}' .ddev/config.yaml)"
fi

ddev_cmd() {
  local subcmd="$1"
  shift
  if [[ -n "${DDEV_PROJECT}" ]]; then
    case "${subcmd}" in
      describe|start)
        ddev "${subcmd}" "${DDEV_PROJECT}" "$@"
        ;;
      *)
        ddev "${subcmd}" --project "${DDEV_PROJECT}" "$@"
        ;;
    esac
  else
    ddev "${subcmd}" "$@"
  fi
}

if ! ddev_cmd describe >/dev/null 2>&1; then
  echo "Starting DDEV (project=${DDEV_PROJECT:-auto})..." >&2
  ddev_cmd start
fi

# Resolve Python with mcp installed (system pip or /opt/venv)
MCP_PYTHON=""
if ddev_cmd exec python3 -c "import mcp" >/dev/null 2>&1; then
  MCP_PYTHON="python3"
elif ddev_cmd exec test -x /opt/venv/bin/python3 && ddev_cmd exec /opt/venv/bin/python3 -c "import mcp" >/dev/null 2>&1; then
  MCP_PYTHON="/opt/venv/bin/python3"
else
  echo "MCP Python deps missing in DDEV web image." >&2
  echo "Run: cp mcp-server/ddev/Dockerfile.mcp .ddev/web-build/Dockerfile.mcp && ddev restart" >&2
  exit 1
fi

exec ddev_cmd exec env \
  PYTHONPATH=/var/www/html/mcp-server/src \
  PROJECT_ROOT=/var/www/html \
  "$MCP_PYTHON" -m orchestrator_mcp.server \
  --transport stdio \
  --project-root /var/www/html