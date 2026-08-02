#!/usr/bin/env bash
# Install Ollama for the active runtime (host, DDEV, or docker-compose).
#
# Usage:
#   bash scripts/install-ollama.sh                    # auto-detect target
#   bash scripts/install-ollama.sh --target host      # force host installer
#   bash scripts/install-ollama.sh --target ddev    # DDEV add-on
#   bash scripts/install-ollama.sh --target docker-compose
#   bash scripts/install-ollama.sh --check-only
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CHECK_ONLY=0
TARGET="auto"

usage() {
  sed -n '2,10p' "$0" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only) CHECK_ONLY=1; shift ;;
    --target)
      TARGET="${2:-}"
      if [[ -z "$TARGET" ]]; then
        printf "[install-ollama] ERROR: --target requires a value\n" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) printf "[install-ollama] ERROR: unknown option: %s\n" "$1" >&2; usage; exit 2 ;;
  esac
done

info() {
  printf "[install-ollama] %s\n" "$1"
}

py=""
if command -v python3 >/dev/null 2>&1; then
  py=python3
elif command -v python >/dev/null 2>&1; then
  py=python
else
  printf "[install-ollama] ERROR: Python 3 required for detection\n" >&2
  exit 1
fi

if [[ "$TARGET" == "auto" ]]; then
  TARGET="$("$py" scripts/ollama_detect.py --root "$ROOT_DIR" --json | "$py" -c 'import json,sys; print(json.load(sys.stdin)["ollama_runtime"])')"
fi

case "$TARGET" in
  host|ddev|docker-compose) ;;
  *)
    printf "[install-ollama] ERROR: invalid --target: %s (use auto|host|ddev|docker-compose)\n" "$TARGET" >&2
    exit 2
    ;;
esac

info "Ollama install target: $TARGET"

extra=()
[[ "$CHECK_ONLY" -eq 1 ]] && extra+=(--check-only)

case "$TARGET" in
  ddev)
    exec bash scripts/install-ollama-ddev.sh "${extra[@]}"
    ;;
  docker-compose)
    exec bash scripts/install-ollama-compose.sh "${extra[@]}"
    ;;
  host)
    ;;
esac

# --- host install (original path) ---
report="$("$py" scripts/ollama_detect.py --root "$ROOT_DIR" --json)"
binary="$(printf '%s' "$report" | "$py" -c 'import json,sys; print(json.load(sys.stdin)["ollama_binary"])')"
api="$(printf '%s' "$report" | "$py" -c 'import json,sys; print(json.load(sys.stdin)["ollama_api"])')"

if [[ "$binary" == "yes" ]]; then
  info "Ollama CLI already installed on host"
  if [[ "$api" == "reachable" ]]; then
    info "Ollama API reachable on host"
  else
    info "Ollama API not reachable — start the service (ollama serve) or open the Ollama app"
  fi
  exit 0
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  info "Host Ollama not installed (check-only)"
  exit 1
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "[install-ollama] ERROR: required command not found: %s\n" >&2
    exit 1
  fi
}

info "Installing Ollama on host via official installer (https://ollama.com)"
require_cmd curl

if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
  info "macOS: trying Homebrew first (brew install ollama)"
  if brew install ollama; then
    info "Ollama installed via Homebrew"
    exit 0
  fi
  info "Homebrew install failed — falling back to official install.sh"
fi

# Download installer to temp file, then execute (avoids remote-pipe anti-pattern)
_installer="$(mktemp "${TMPDIR:-/tmp}/ollama-install.XXXXXX.sh")"
trap 'rm -f "${_installer}"' EXIT
info "Downloading official installer to ${_installer}"
curl -fsSL https://ollama.com/install.sh -o "${_installer}"
# Minimal integrity: non-empty script that mentions ollama
if [[ ! -s "${_installer}" ]] || ! grep -qi 'ollama' "${_installer}"; then
  printf "[install-ollama] ERROR: downloaded installer looks invalid\n" >&2
  exit 1
fi
chmod +x "${_installer}"
info "Running official Ollama installer (review: https://ollama.com)"
bash "${_installer}"

report="$("$py" scripts/ollama_detect.py --root "$ROOT_DIR" --json)"
binary="$(printf '%s' "$report" | "$py" -c 'import json,sys; print(json.load(sys.stdin)["ollama_binary"])')"
if [[ "$binary" != "yes" ]]; then
  printf "[install-ollama] ERROR: install finished but ollama CLI still not on PATH\n" >&2
  exit 1
fi

info "Ollama installed on host — verify with: ollama --version"
info "Pull a model: ollama pull llama3.2"
info "Docs: docs/guides/local-ollama.md"