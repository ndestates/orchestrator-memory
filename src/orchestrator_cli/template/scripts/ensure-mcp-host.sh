#!/usr/bin/env bash
# ensure-mcp-host.sh — preflight / repair host stdio MCP (mcp-server/.venv).
#
# Makes orchestrator-host MCP available before Grok/Cursor connect, so session-start
# and first tool call do not fail on a missing or broken venv.
#
# Usage:
#   bash scripts/ensure-mcp-host.sh              # check + repair if needed
#   bash scripts/ensure-mcp-host.sh --check      # status only (exit 1 if not ready)
#   bash scripts/ensure-mcp-host.sh --force      # rebuild venv even if healthy
#   bash scripts/ensure-mcp-host.sh --quiet      # less chatter (for launchers)
#   bash scripts/ensure-mcp-host.sh --json       # one JSON line for agents
#
# Exit: 0 ready · 1 not ready · 2 usage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer repo root of this script (works even when cwd is wrong / git fails)
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi

CHECK_ONLY=0
FORCE=0
QUIET=0
JSON=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --force|--repair) FORCE=1 ;;
    --quiet|-q) QUIET=1 ;;
    --json) JSON=1 ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      echo "ensure-mcp-host: unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

info() { [[ "$QUIET" -eq 1 || "$JSON" -eq 1 ]] || printf "[ensure-mcp] %s\n" "$1"; }
warn() { printf "[ensure-mcp] WARN: %s\n" "$1" >&2; }
err()  { printf "[ensure-mcp] ERROR: %s\n" "$1" >&2; }

VENV="$ROOT/mcp-server/.venv"
PY="$VENV/bin/python"
BIN="$VENV/bin/orchestrator-mcp"
PKG="$ROOT/mcp-server"

emit_json() {
  local ready="$1" note="$2"
  python3 -c 'import json,sys; print(json.dumps({"mcp_host_ready":sys.argv[1]=="yes","ready":sys.argv[1],"note":sys.argv[2],"root":sys.argv[3],"venv":sys.argv[4],"bin":sys.argv[5]}))' \
    "$ready" "$note" "$ROOT" "$VENV" "$BIN"
}

find_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
  elif [[ -x "${HOME}/.local/bin/uv" ]]; then
    echo "${HOME}/.local/bin/uv"
  else
    echo ""
  fi
}

venv_healthy() {
  [[ -x "$BIN" ]] || return 1
  [[ -x "$PY" ]] || return 1
  # Import path used by the server — catches half-broken uv venvs (no pip, stale deps)
  "$PY" -c "import mcp; import yaml; import orchestrator_mcp" >/dev/null 2>&1
}

drop_venv() {
  if [[ -d "$VENV" ]]; then
    info "removing broken/forced venv: $VENV"
    rm -rf "$VENV"
  fi
}

bootstrap_uv() {
  local uv
  uv="$(find_uv)"
  if [[ -z "$uv" ]]; then
    return 1
  fi
  info "bootstrapping mcp-server/.venv with uv ($uv)"
  "$uv" venv "$VENV"
  # Install package + deps into the venv (no system ensurepip needed)
  "$uv" pip install -e "$PKG" --python "$PY"
  return 0
}

bootstrap_venv_pip() {
  if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    return 1
  fi
  info "bootstrapping mcp-server/.venv with python3 -m venv + pip"
  python3 -m venv "$VENV"
  # Prefer python -m pip (more reliable than bare pip binary)
  "$PY" -m pip install -q -U pip
  "$PY" -m pip install -q -e "$PKG"
  return 0
}

print_fix() {
  cat >&2 <<EOF
ensure-mcp-host: cannot build mcp-server/.venv under $ROOT

Need one of:
  • uv on PATH  (https://docs.astral.sh/uv/)  — preferred when ensurepip missing
  • python3-venv / ensurepip:
      sudo apt-get install -y python3-venv python3.12-venv

Then re-run:
  bash scripts/ensure-mcp-host.sh
  # or let session-start / mcp-host-stdio.sh repair on connect

Grok: [mcp_servers.orchestrator-host] enabled in .grok/config.toml
EOF
}

# --- main ---
if [[ ! -d "$PKG/src/orchestrator_mcp" ]]; then
  err "mcp-server package missing at $PKG"
  [[ "$JSON" -eq 1 ]] && emit_json "no" "mcp-server package missing"
  exit 1
fi

if [[ "$FORCE" -eq 1 ]]; then
  drop_venv
elif ! venv_healthy; then
  if [[ -d "$VENV" ]]; then
    warn "venv present but unhealthy — repairing"
    drop_venv
  fi
fi

if venv_healthy; then
  note="ok"
  info "ready: $BIN"
  [[ "$JSON" -eq 1 ]] && emit_json "yes" "$note"
  exit 0
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  note="mcp-server/.venv missing or unhealthy"
  warn "$note"
  [[ "$JSON" -eq 1 ]] && emit_json "no" "$note"
  exit 1
fi

# Repair path: uv first (works without ensurepip), then venv+pip
if ! bootstrap_uv; then
  if ! bootstrap_venv_pip; then
    print_fix
    [[ "$JSON" -eq 1 ]] && emit_json "no" "cannot bootstrap venv (need uv or python3-venv)"
    exit 1
  fi
fi

if ! venv_healthy; then
  err "bootstrap finished but imports still fail"
  "$PY" -c "import mcp; import yaml; import orchestrator_mcp" 2>&1 | head -20 >&2 || true
  [[ "$JSON" -eq 1 ]] && emit_json "no" "imports failed after bootstrap"
  exit 1
fi

info "ready after repair: $BIN"
[[ "$JSON" -eq 1 ]] && emit_json "yes" "repaired"
exit 0
