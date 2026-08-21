#!/usr/bin/env bash
# Host stdio MCP for orchestrator template repo (no DDEV). Used by .grok/config.toml.
#
# Always resolves PROJECT_ROOT from this script’s location (not fragile git-only ROOT),
# then ensures mcp-server/.venv is healthy before exec (uv or python3-venv).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi
export PROJECT_ROOT="$ROOT"

ENSURE="${ROOT}/scripts/ensure-mcp-host.sh"
if [[ ! -f "$ENSURE" ]]; then
  echo "mcp-host-stdio: missing $ENSURE" >&2
  exit 1
fi

# Repair quietly so Grok MCP connect does not die on first-run / broken venv
if ! bash "$ENSURE" --quiet; then
  echo "mcp-host-stdio: ensure-mcp-host failed — run: bash scripts/ensure-mcp-host.sh" >&2
  exit 1
fi

BIN="${ROOT}/mcp-server/.venv/bin/orchestrator-mcp"
if [[ ! -x "$BIN" ]]; then
  echo "mcp-host-stdio: $BIN missing after ensure" >&2
  exit 1
fi

exec "$BIN" --transport stdio --project-root "$ROOT"
