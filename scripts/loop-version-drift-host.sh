#!/usr/bin/env bash
# L1 host snapshot for version-drift-watch (read-only). No upgrades.
# Usage: bash scripts/loop-version-drift-host.sh
# Optional: ORCHESTRATOR_APPS="ndestates-io lightstone e-ndsign" (or legacy WAVE_APPS)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DAY="$(date -u +%Y-%m-%d)"
OUT="reports/loops/${DAY}-version-drift-host.md"
mkdir -p reports/loops
PROJECTS="${PROJECTS_ROOT:-$HOME/projects}"

TEMPLATE_VER="$(tr -d '[:space:]' <"${ROOT}/VERSION" 2>/dev/null || echo unknown)"

# Default sibling-app list (fleet wave inventory removed permanently)
APP_LIST="${ORCHESTRATOR_APPS:-${WAVE_APPS:-}}"
if [[ -n "$APP_LIST" ]]; then
  # shellcheck disable=SC2206
  APPS=( $APP_LIST )
else
  APPS=(ndestates-io e-ndsign jerseyhouseprices lightstone mailchimp facebook-stats google-stats ndestates)
fi
if [[ ${#APPS[@]} -eq 0 ]]; then
  APPS=(ndestates-io e-ndsign jerseyhouseprices lightstone mailchimp facebook-stats google-stats ndestates)
fi

{
  echo "# Version drift host snapshot — ${DAY}"
  echo
  echo "**Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "**Template VERSION:** \`${TEMPLATE_VER}\`"
  echo "**Projects root:** \`${PROJECTS}\`"
  echo
  echo "| App | Lock | Status | Branch | Dirty |"
  echo "|-----|------|--------|--------|-------|"
  for app in "${APPS[@]}"; do
    p="${PROJECTS}/${app}"
    if [[ ! -d "$p" ]]; then
      echo "| ${app} | — | missing | — | — |"
      continue
    fi
    lock="none"
    if [[ -f "${p}/.orchestrator-version" ]]; then
      lock="$(python3 -c "import json;print(json.load(open('${p}/.orchestrator-version')).get('version','?'))" 2>/dev/null || echo '?')"
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
  echo "Report-only. Per-app upgrade only: \`orchestrator upgrade /path/to/app --no-pr\`."
  echo "Fleet wave tooling is permanently removed — never reintroduce multi-app wave deploy."
} >"$OUT"

echo "Wrote $OUT"
