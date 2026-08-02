#!/usr/bin/env bash
# install-host-tools.sh — ensure host CLI tools the orchestrator depends on.
#
# Primary tool: **ripgrep (rg)** — used by:
#   - Cyber Essentials lean scan (.grok/skills/.../cyber-essentials-scan.sh)
#   - session-security-sweep (session-start)
#   - agents / cache-first grep-before-read workflows
#
# Without rg, CSE silently skips several controls ("rg not available — skipped").
#
# Usage:
#   bash scripts/install-host-tools.sh              # check; install missing if possible
#   bash scripts/install-host-tools.sh --check      # exit 0 all present, 1 if missing
#   bash scripts/install-host-tools.sh --yes        # non-interactive install (CI / bootstrap)
#   bash scripts/install-host-tools.sh --dry-run    # print planned actions only
#   bash scripts/install-host-tools.sh --list       # show required tools + status
#
# Environments:
#   Host (Linux distro, WSL2, macOS Homebrew) — this script
#   DDEV web container — see mcp-server/ddev/ (webimage_extra_packages or Dockerfile)
#   Docker image builds — apt-get install ripgrep in your Dockerfile
#
# Exit: 0 success (or check OK); 1 missing after attempt; 2 usage error
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHECK_ONLY=0
YES=0
DRY_RUN=0
LIST=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --yes|-y) YES=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --list) LIST=1 ;;
    -h|--help)
      sed -n '2,28p' "$0"
      exit 0
      ;;
    *)
      printf "[host-tools] ERROR: unknown argument: %s\n" "$arg" >&2
      exit 2
      ;;
  esac
done

info() { printf "[host-tools] %s\n" "$1"; }
warn() { printf "[host-tools] WARN: %s\n" "$1" >&2; }
err()  { printf "[host-tools] ERROR: %s\n" "$1" >&2; }

# tool_id → binary name
# shellcheck disable=SC2034
REQUIRED_TOOLS=(ripgrep)

tool_bin() {
  case "$1" in
    ripgrep) echo rg ;;
    *) echo "$1" ;;
  esac
}

tool_present() {
  local bin
  bin="$(tool_bin "$1")"
  command -v "$bin" >/dev/null 2>&1
}

tool_version() {
  local bin
  bin="$(tool_bin "$1")"
  if command -v "$bin" >/dev/null 2>&1; then
    "$bin" --version 2>/dev/null | head -n1 || echo "present"
  else
    echo "MISSING"
  fi
}

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    echo apt
  elif command -v dnf >/dev/null 2>&1; then
    echo dnf
  elif command -v yum >/dev/null 2>&1; then
    echo yum
  elif command -v pacman >/dev/null 2>&1; then
    echo pacman
  elif command -v apk >/dev/null 2>&1; then
    echo apk
  elif command -v brew >/dev/null 2>&1; then
    echo brew
  elif command -v zypper >/dev/null 2>&1; then
    echo zypper
  else
    echo none
  fi
}

pkg_name_for() {
  # package name per manager (most use ripgrep)
  local tool="$1" mgr="$2"
  case "$tool" in
    ripgrep)
      case "$mgr" in
        apt|dnf|yum|apk|brew|zypper|pacman) echo ripgrep ;;
        *) echo ripgrep ;;
      esac
      ;;
    *) echo "$tool" ;;
  esac
}

run_install() {
  local mgr="$1" pkg="$2"
  local cmd=()

  case "$mgr" in
    apt)
      if [[ "$DRY_RUN" -eq 1 ]]; then
        if [[ "$(id -u)" -eq 0 ]]; then
          info "dry-run: apt-get update && apt-get install -y --no-install-recommends $pkg"
        else
          info "dry-run: sudo apt-get update && sudo apt-get install -y --no-install-recommends $pkg"
        fi
        return 0
      fi
      if [[ "$(id -u)" -eq 0 ]]; then
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$pkg"
      else
        if ! sudo -n true 2>/dev/null; then
          err "need passwordless sudo or run as root to install via apt"
          info "manual: sudo apt-get update && sudo apt-get install -y ripgrep"
          return 1
        fi
        sudo apt-get update -qq
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$pkg"
      fi
      ;;
    dnf)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: sudo dnf install -y $pkg"; return 0; fi
      sudo dnf install -y "$pkg"
      ;;
    yum)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: sudo yum install -y $pkg"; return 0; fi
      sudo yum install -y "$pkg"
      ;;
    pacman)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: sudo pacman -S --noconfirm $pkg"; return 0; fi
      sudo pacman -S --noconfirm "$pkg"
      ;;
    apk)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: apk add --no-cache $pkg"; return 0; fi
      if [[ "$(id -u)" -eq 0 ]]; then
        apk add --no-cache "$pkg"
      else
        sudo apk add --no-cache "$pkg"
      fi
      ;;
    brew)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: brew install $pkg"; return 0; fi
      brew install "$pkg"
      ;;
    zypper)
      if [[ "$DRY_RUN" -eq 1 ]]; then info "dry-run: sudo zypper install -y $pkg"; return 0; fi
      sudo zypper install -y "$pkg"
      ;;
    none)
      err "no supported package manager found"
      print_manual_hints
      return 1
      ;;
    *)
      err "unsupported package manager: $mgr"
      return 1
      ;;
  esac
}

print_manual_hints() {
  cat <<'EOF' >&2
[host-tools] Install ripgrep (rg) manually:

  # Debian / Ubuntu / WSL2 (recommended on WSL)
  sudo apt-get update && sudo apt-get install -y ripgrep

  # Fedora / RHEL
  sudo dnf install -y ripgrep

  # Arch
  sudo pacman -S ripgrep

  # Alpine (Docker/DDEV base sometimes)
  sudo apk add ripgrep

  # macOS
  brew install ripgrep

  # Windows (PowerShell)
  winget install BurntSushi.ripgrep.MSVC
  # or: choco install ripgrep
  # or: .\scripts\install-host-tools.ps1 -Yes

  # DDEV web container (Laravel/PHP apps) — prefer config, not one-off apt:
  #   in .ddev/config.yaml:
  #     webimage_extra_packages: [ripgrep]
  #   then: ddev restart
  # Or copy mcp-server/ddev/Dockerfile.tools → .ddev/web-build/Dockerfile.tools

  # Generic Dockerfile
  #   RUN apt-get update && apt-get install -y --no-install-recommends ripgrep \
  #     && rm -rf /var/lib/apt/lists/*

  Docs: docs/getting-started/installation.md#host-tools-ripgrep
EOF
}

missing=()
for t in "${REQUIRED_TOOLS[@]}"; do
  if tool_present "$t"; then
    info "OK $(tool_bin "$t"): $(tool_version "$t")"
  else
    info "MISSING $(tool_bin "$t") ($t)"
    missing+=("$t")
  fi
done

if [[ "$LIST" -eq 1 ]]; then
  [[ ${#missing[@]} -eq 0 ]] && exit 0 || exit 1
fi

if [[ ${#missing[@]} -eq 0 ]]; then
  info "all required host tools present"
  exit 0
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  warn "missing: ${missing[*]}"
  print_manual_hints
  exit 1
fi

if [[ "$YES" -ne 1 && "$DRY_RUN" -ne 1 ]]; then
  if [[ ! -t 0 ]]; then
    warn "non-interactive shell and missing tools — re-run with --yes to install"
    print_manual_hints
    exit 1
  fi
  printf "[host-tools] Install missing tools (%s)? [y/N] " "${missing[*]}"
  read -r ans || ans=n
  case "$ans" in
    y|Y|yes|YES) ;;
    *)
      info "skipped install"
      print_manual_hints
      exit 1
      ;;
  esac
fi

mgr="$(detect_pkg_manager)"
info "package manager: $mgr"
failed=0
for t in "${missing[@]}"; do
  pkg="$(pkg_name_for "$t" "$mgr")"
  info "installing $t (package: $pkg)"
  if ! run_install "$mgr" "$pkg"; then
    failed=1
    continue
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    continue
  fi
  if tool_present "$t"; then
    info "OK $(tool_bin "$t"): $(tool_version "$t")"
  else
    err "installed $pkg but $(tool_bin "$t") still not on PATH"
    failed=1
  fi
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  info "dry-run complete"
  exit 0
fi

if [[ "$failed" -ne 0 ]] || ! tool_present ripgrep; then
  print_manual_hints
  exit 1
fi

info "host tools ready"
exit 0
