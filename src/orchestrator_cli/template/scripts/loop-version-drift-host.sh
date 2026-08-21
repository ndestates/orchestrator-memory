#!/usr/bin/env bash
# L1 host snapshot for version-drift-watch (read-only). No upgrades.
# Product rule: **active project only** by default (never walk ~/projects fleet).
# Usage: bash scripts/loop-version-drift-host.sh
# Optional multi-app (explicit opt-in only):
#   ORCHESTRATOR_APPS="app1 app2"  and  PROJECTS_ROOT=~/projects
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DAY="$(date -u +%Y-%m-%d)"
OUT="reports/loops/${DAY}-version-drift-host.md"
mkdir -p reports/loops
PROJECTS="${PROJECTS_ROOT:-$HOME/projects}"
SELF_NAME="$(basename "$ROOT")"

TEMPLATE_VER="$(tr -d '[:space:]' <"${ROOT}/VERSION" 2>/dev/null || echo unknown)"

# Default: this repo only. Multi-app only when operator sets ORCHESTRATOR_APPS explicitly.
APP_LIST="${ORCHESTRATOR_APPS:-}"
if [[ -n "$APP_LIST" ]]; then
  # shellcheck disable=SC2206
  APPS=( $APP_LIST )
else
  APPS=("${SELF_NAME}")
fi

{
  echo "# Version drift host snapshot — ${DAY}"
  echo
  echo "**Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "**Template VERSION:** \`${TEMPLATE_VER}\`"
  echo "**Scope:** active project only (set ORCHESTRATOR_APPS for multi-app opt-in)"
  echo "**Self:** \`${ROOT}\`"
  if [[ -n "${ORCHESTRATOR_APPS:-}" ]]; then
    echo "**Projects root (opt-in):** \`${PROJECTS}\`"
  fi
  echo
  echo "| App | Lock | Status | Branch | Dirty |"
  echo "|-----|------|--------|--------|-------|"
  for app in "${APPS[@]}"; do
    # Active self: always use ROOT. Opt-in list: PROJECTS/<app>.
    if [[ "$app" == "$SELF_NAME" ]]; then
      p="$ROOT"
    else
      p="${PROJECTS}/${app}"
    fi
    if [[ ! -d "$p" ]]; then
      echo "| ${app} | — | missing | — | — |"
      continue
    fi
    lock="none"
    if [[ -f "${p}/.orchestrator-version" ]]; then
      lock="$(python3 -c "import json;print(json.load(open('${p}/.orchestrator-version')).get('version','?'))" 2>/dev/null || echo '?')"
    elif [[ -f "${p}/VERSION" ]]; then
      lock="$(tr -d '[:space:]' <"${p}/VERSION" 2>/dev/null || echo '?')"
    fi
    br="$(git -C "$p" branch --show-current 2>/dev/null || echo '?')"
    dirty_n="$(git -C "$p" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$lock" == "none" ]]; then
      st="no_lock"
    elif [[ "$lock" == "$TEMPLATE_VER" ]]; then
      st="current"
    else
      st="behind"
    fi
    echo "| ${app} | ${lock} | ${st} | \`${br}\` | ${dirty_n} |"
  done
  echo
  echo "## L1 note"
  echo
  echo "Report-only. Active project only by default. Per-app upgrade: \`orchestrator upgrade /path/to/app --no-pr\`."
  echo "Fleet wave tooling is permanently removed — never reintroduce multi-app wave deploy or default fleet lists."
} >"$OUT"

echo "Wrote $OUT"
