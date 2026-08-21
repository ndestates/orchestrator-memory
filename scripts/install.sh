#!/usr/bin/env bash
# Orchestrator template bootstrap (Linux / macOS).
# Usage:
#   bash scripts/install.sh              # dirs + manifests + validation + host tools check
#   bash scripts/install.sh --uv-tool    # **preferred** host CLI: uv tool install (survives git branches)
#   bash scripts/install.sh --cli        # pip install -e . (user/site; may need pip)
#   bash scripts/install.sh --npm        # Node wrapper via npm install -g (→ Python CLI)
#   bash scripts/install.sh --pnpm       # Node wrapper via pnpm add -g (same package; use if you use pnpm)
#   bash scripts/install.sh --node       # Node wrapper: prefer pnpm if on PATH, else npm
#   bash scripts/install.sh --cli --npm  # Python + Node
#   bash scripts/install.sh --host-tools # install ripgrep (rg) if missing (non-interactive)
#   bash scripts/install.sh --mcp        # ensure host MCP venv (mcp-server/.venv) is ready
#   bash scripts/install.sh --ollama     # optional local Ollama (BYOM) — host/DDEV/compose
#
# Host package vs in-app:
#   --uv-tool / --cli / --npm / --pnpm / --node  → machine-global CLI (persists across branches)
#   orchestrator init/upgrade  → template surfaces *inside* one app repo (git-tracked)
#
# Per-app install into another repo (not fleet wave):
#   orchestrator init /path/to/app --no-pr
# See docs/getting-started/installation.md, docs/guides/local-ollama.md, docs/reference/licensing.md
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INSTALL_CLI=0
INSTALL_UV_TOOL=0
INSTALL_NPM=0
INSTALL_PNPM=0
INSTALL_NODE=0
INSTALL_OLLAMA=0
INSTALL_HOST_TOOLS=0
INSTALL_MCP=0
for arg in "$@"; do
  case "$arg" in
    --cli) INSTALL_CLI=1 ;;
    --uv-tool|--uv) INSTALL_UV_TOOL=1 ;;
    --npm) INSTALL_NPM=1 ;;
    --pnpm) INSTALL_PNPM=1 ;;
    --node) INSTALL_NODE=1 ;;
    --ollama) INSTALL_OLLAMA=1 ;;
    --host-tools) INSTALL_HOST_TOOLS=1 ;;
    --mcp) INSTALL_MCP=1 ;;
    -h|--help)
      sed -n '2,24p' "$0"
      exit 0
      ;;
    *)
      printf "[install] ERROR: unknown argument: %s\n" "$arg" >&2
      exit 2
      ;;
  esac
done

info() {
  printf "[install] %s\n" "$1"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf "[install] ERROR: required command not found: %s\n" "$cmd" >&2
    exit 1
  fi
}

info "Checking required commands"
require_cmd bash
require_cmd git
require_cmd python3

if [[ ! -d .git ]]; then
  printf "[install] ERROR: run this script from inside the repository (missing .git).\n" >&2
  exit 1
fi

# ripgrep (rg): CSE + session-security-sweep + agent search. Soft-required.
if [[ -f scripts/install-host-tools.sh ]]; then
  if [[ "$INSTALL_HOST_TOOLS" -eq 1 ]]; then
    info "Ensuring host tools (ripgrep) — scripts/install-host-tools.sh --yes"
    bash scripts/install-host-tools.sh --yes || {
      printf "[install] WARN: host tools install incomplete — CSE may skip controls\n" >&2
    }
  else
    info "Checking host tools (ripgrep); install with: bash scripts/install.sh --host-tools"
    if ! bash scripts/install-host-tools.sh --check >/dev/null 2>&1; then
      printf "[install] WARN: rg (ripgrep) missing — CSE session scan skips some controls\n" >&2
      printf "[install]        fix: bash scripts/install-host-tools.sh --yes\n" >&2
      printf "[install]        WSL/Debian: sudo apt-get install -y ripgrep\n" >&2
      printf "[install]        DDEV: webimage_extra_packages: [ripgrep] then ddev restart\n" >&2
      printf "[install]        see docs/getting-started/installation.md#host-tools-ripgrep\n" >&2
    else
      info "OK host tools: rg present"
    fi
  fi
fi

info "Creating expected directory structure"
mkdir -p .github/agents
mkdir -p .github/prompts
mkdir -p docs/codebase
mkdir -p TODO

info "Syncing per-platform manifests"
if [[ -f scripts/sync_manifests.py ]]; then
  python3 scripts/sync_manifests.py
fi

info "Validating required template files"
required_files=(
  ".github/project-manifest.yaml"
  ".grok/project-manifest.yaml"
  "docs/codebase/README.md"
  "LICENSE"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    printf "[install] ERROR: required file missing: %s\n" "$file" >&2
    exit 1
  fi
  info "Found $file"
done

# Host CLI package — lives outside git; survives branch switches and repo checkouts.
# Prefer --uv-tool when uv is available (isolated tool env; no system pip required).
if [[ "$INSTALL_UV_TOOL" -eq 1 ]]; then
  info "Installing host CLI via uv tool (package persists across branches)"
  UV_BIN=""
  if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
  elif [[ -x "${HOME}/.local/bin/uv" ]]; then
    UV_BIN="${HOME}/.local/bin/uv"
  fi
  if [[ -z "$UV_BIN" ]]; then
    printf "[install] ERROR: uv not found. Install: https://docs.astral.sh/uv/\n" >&2
    printf "[install]        or use: bash scripts/install.sh --cli\n" >&2
    exit 1
  fi
  "$UV_BIN" tool install --force --from "$ROOT_DIR" orchestrator
  if command -v orchestrator >/dev/null 2>&1; then
    orchestrator version || true
    info "OK: host package on PATH (uv tool) — not tied to any git branch"
  else
    info "Note: ensure ~/.local/bin is on PATH (uv tool bin)"
  fi
fi

if [[ "$INSTALL_CLI" -eq 1 ]]; then
  info "Installing orchestrator CLI package (pip editable)"
  if python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install -e .
  elif command -v uv >/dev/null 2>&1; then
    info "system pip missing — using: uv pip install -e . --system (or prefer --uv-tool)"
    uv pip install -e "$ROOT_DIR" 2>/dev/null || uv pip install --python python3 -e "$ROOT_DIR"
  else
    printf "[install] ERROR: neither pip nor uv available for --cli\n" >&2
    printf "[install]        Prefer: bash scripts/install.sh --uv-tool\n" >&2
    exit 1
  fi
  if command -v orchestrator >/dev/null 2>&1; then
    orchestrator version
  else
    info "Note: 'orchestrator' not on PATH yet — using module form"
    PYTHONPATH=src python3 -m orchestrator_cli version
  fi
fi

# Node wrapper: @ndestates/orchestrator (package.json) → Python CLI via postinstall.
# Prefer pnpm when --pnpm or --node and pnpm is on PATH (same host package, branch-independent).
install_node_wrapper() {
  local manager="$1" # npm | pnpm
  info "Installing Node package wrapper via ${manager} (delegates to Python CLI; host-global)"
  require_cmd "$manager"
  case "$manager" in
    pnpm)
      # Global add from this checkout; postinstall installs/refreshes Python CLI
      if ! pnpm add -g "$ROOT_DIR"; then
        # Older pnpm: file: protocol
        pnpm add -g "file:${ROOT_DIR}"
      fi
      ;;
    npm)
      # postinstall runs pip install when from git checkout
      npm install -g "$ROOT_DIR"
      ;;
    *)
      printf "[install] ERROR: unknown node package manager: %s\n" "$manager" >&2
      return 1
      ;;
  esac
  if command -v orchestrator >/dev/null 2>&1; then
    orchestrator version || true
    info "OK: host package on PATH (${manager}) — not tied to app feature branches"
  else
    info "Note: orchestrator not on PATH — ensure ${manager} global bin is on PATH"
    if [[ "$manager" == "pnpm" ]]; then
      info "        pnpm bin -g   # add this directory to PATH"
    else
      info "        npm bin -g    # add this directory to PATH"
    fi
  fi
}

if [[ "$INSTALL_NODE" -eq 1 ]]; then
  if command -v pnpm >/dev/null 2>&1; then
    install_node_wrapper pnpm
  elif command -v npm >/dev/null 2>&1; then
    install_node_wrapper npm
  else
    printf "[install] ERROR: --node requires pnpm or npm on PATH\n" >&2
    exit 1
  fi
fi

if [[ "$INSTALL_PNPM" -eq 1 ]]; then
  install_node_wrapper pnpm
fi

if [[ "$INSTALL_NPM" -eq 1 ]]; then
  install_node_wrapper npm
fi

info "Setting up operator profile (who-i-am) if missing"
if [[ -f scripts/setup-who-i-am.sh ]]; then
  bash scripts/setup-who-i-am.sh || true
fi

# Host MCP (stdio) — DISABLED by default (not required for CLI/chains/cache-first).
# Opt-in only: bash scripts/install.sh --mcp  and  ORCHESTRATOR_MCP=1 / runtime.mcp: dev_only
if [[ -d mcp-server/src/orchestrator_mcp && -f scripts/ensure-mcp-host.sh ]]; then
  if [[ "$INSTALL_MCP" -eq 1 ]]; then
    info "Ensuring host MCP venv (explicit --mcp; product default is MCP off)"
    bash scripts/ensure-mcp-host.sh || {
      printf "[install] WARN: MCP host ensure failed — bash scripts/ensure-mcp-host.sh\n" >&2
    }
  else
    info "MCP skipped (default off). Opt-in: bash scripts/install.sh --mcp + ORCHESTRATOR_MCP=1"
  fi
fi

if [[ "$INSTALL_OLLAMA" -eq 1 ]]; then
  info "Installing local Ollama (optional BYOM — host / DDEV / docker-compose)"
  if [[ -f scripts/install-ollama.sh ]]; then
    bash scripts/install-ollama.sh
  else
    printf "[install] ERROR: scripts/install-ollama.sh missing\n" >&2
    exit 1
  fi
fi

info "Installation checks completed successfully"
info "Next: edit .grok/memories/who-i-am.md then /chain session-start"
info "Host CLI package (branch-independent): bash scripts/install.sh --uv-tool   # preferred"
info "  refresh later: orchestrator self-upgrade --yes   or  bash scripts/install.sh --uv-tool"
info "Per-app template (git files in one app): orchestrator init /path/to/app --no-pr"
info "Host tools (rg): bash scripts/install.sh --host-tools  or  bash scripts/install-host-tools.sh --yes"
info "Host MCP (optional, default off): bash scripts/install.sh --mcp  + ORCHESTRATOR_MCP=1"
info "Optional Ollama: bash scripts/install.sh --ollama  (see docs/guides/local-ollama.md)"
info "Docs: docs/getting-started/installation.md | licensing: docs/reference/licensing.md"
