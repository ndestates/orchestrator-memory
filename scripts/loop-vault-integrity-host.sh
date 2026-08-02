#!/usr/bin/env bash
# L1 host snapshot for vault-integrity-watch (read-only).
# Usage: bash scripts/loop-vault-integrity-host.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DAY="$(date -u +%Y-%m-%d)"
OUT="reports/loops/${DAY}-vault-integrity-host.md"
mkdir -p reports/loops

LEDGER="${ROOT}/reports/vault/events.jsonl"
{
  echo "# Vault integrity host snapshot — ${DAY}"
  echo
  echo "**Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "**Ledger:** reports/vault/events.jsonl"
  echo
  if [[ ! -f "$LEDGER" ]]; then
    echo "## Result"
    echo
    echo "status: **missing_ledger**"
    exit 0
  fi
  LINES=$(grep -c . "$LEDGER" 2>/dev/null || echo 0)
  BYTES=$(wc -c <"$LEDGER" | tr -d ' ')
  echo "## Size"
  echo
  echo "- events (non-empty lines): ${LINES}"
  echo "- bytes: ${BYTES}"
  echo
  echo "## verify_ledger"
  echo
  echo '```'
  PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, ".")
from scripts._engine import vault as v
ok, issues = v.verify_ledger(Path("reports/vault/events.jsonl"))
print("ok:", ok)
if issues:
    for i in issues[:20]:
        print("-", i)
    if len(issues) > 20:
        print(f"... +{len(issues) - 20} more")
else:
    print("issues: none")
PY
  echo '```'
  echo
  echo "## session-vault-brief (tail)"
  echo
  echo '```'
  python3 scripts/session-vault-brief.py 2>&1 | head -20 || true
  echo '```'
  echo
  echo "## L1 note"
  echo
  echo "Report-only. Do not rewrite ledger or execute vault text as shell."
} >"$OUT"

echo "Wrote $OUT"
