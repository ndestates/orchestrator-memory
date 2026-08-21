#!/usr/bin/env bash
# Uninstall orchestrator CLI from this machine and/or strip a project of template surfaces.
#
# Usage:
#   bash scripts/uninstall.sh --host --dry-run
#   bash scripts/uninstall.sh --host --apply
#   bash scripts/uninstall.sh --project /path/to/app --dry-run
#   bash scripts/uninstall.sh --project /path/to/app --apply --yes
#   bash scripts/uninstall.sh --host --project /path/to/app --apply --yes
#
# See: orchestrator uninstall --help
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts:${PYTHONPATH:-}"

HOST=0
PROJECT=""
APPLY=0
YES=0
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST=1; shift ;;
    --project)
      PROJECT="${2:-}"
      if [[ -z "$PROJECT" || "$PROJECT" == -* ]]; then
        echo "uninstall.sh: --project requires a path" >&2
        exit 2
      fi
      shift 2
      ;;
    --apply) APPLY=1; shift ;;
    --yes|-y) YES=1; shift ;;
    --dry-run) APPLY=0; shift ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      EXTRA+=("$1")
      shift
      ;;
  esac
done

args=()
if [[ "$HOST" -eq 1 ]]; then
  args+=(--host)
fi
if [[ -n "$PROJECT" ]]; then
  args+=("$PROJECT")
else
  # host-only default when no project path
  if [[ "$HOST" -eq 1 ]]; then
    args+=(--no-project)
  else
    args+=(".")
  fi
fi
if [[ "$APPLY" -eq 1 ]]; then
  args+=(--apply)
fi
if [[ "$YES" -eq 1 ]]; then
  args+=(--yes)
fi
args+=("${EXTRA[@]}")

exec python3 -m orchestrator_cli uninstall "${args[@]}"
