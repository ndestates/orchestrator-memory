#!/usr/bin/env bash
# Run the reference license validate server (POST /api/licenses/validate).
# Usage:
#   bash scripts/license-validate-server.sh
#   ORCHESTRATOR_LICENSE_ALLOWLIST=dev-key-1 ORCHESTRATOR_LICENSE_FIRST_PARTY=dev-key-1 \
#     bash scripts/license-validate-server.sh
#   ORCHESTRATOR_LICENSE_DEV_ACCEPT_ANY=1 bash scripts/license-validate-server.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/src:${PYTHONPATH:-}"
exec python3 -m orchestrator_cli.license_server "$@"
