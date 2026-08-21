#!/usr/bin/env bash
# Per-app orchestrator template updater (replaces fleet wave deploy for routine updates).
#
# Usage:
#   bash scripts/orchestrator-app-update.sh /path/to/app [--dry-run] [--no-pr] [--to VERSION]
#   bash scripts/orchestrator-app-update.sh /path/to/app --selections grok,chains,scripts
#
# Wraps: python3 -m orchestrator_cli upgrade
set -euo pipefail

ORCH="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ORCH"

target="${1:-}"
if [[ -z "$target" || "$target" == -* ]]; then
  sed -n '2,12p' "$0" >&2
  exit 2
fi
shift || true

export PYTHONPATH="${ORCH}/src:${ORCH}/scripts:${PYTHONPATH:-}"
exec python3 -m orchestrator_cli upgrade "$target" "$@"