#!/usr/bin/env bash
# List GitHub workflows and map to local files.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI required" >&2
  exit 1
fi

echo "=== Remote workflows (gh) ==="
gh workflow list

echo ""
echo "=== Local workflow files ==="
if [[ -d .github/workflows ]]; then
  ls -1 .github/workflows/*.{yml,yaml} 2>/dev/null || ls -1 .github/workflows/ 2>/dev/null || true
else
  echo "(no .github/workflows directory)"
fi