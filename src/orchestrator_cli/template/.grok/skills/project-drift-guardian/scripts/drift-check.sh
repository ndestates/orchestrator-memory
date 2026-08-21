#!/usr/bin/env bash
# Generic drift check: git vs develop/master, skill-health scan, cache freshness.
# Exit 1 when skill-health scan reports stale covers (cache drift is advisory).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

BRANCH="${1:-$(git branch --show-current)}"
SCOPE="${2:-skill-contract + cache + scope}"
REPORT_DIR="reports/drift"
mkdir -p "$REPORT_DIR"

echo "=== Drift check ==="
echo "Branch: $BRANCH"
echo "Scope: $SCOPE"
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

BASE="origin/develop"
if ! git rev-parse --verify --quiet "$BASE" >/dev/null; then
  BASE="origin/master"
fi

echo ">> Git vs $BASE"
git diff --stat "${BASE}...HEAD" 2>/dev/null | head -20 || true
echo

SKILL_SCAN=0
if [[ -f scripts/skill_health.py ]]; then
  echo ">> Skill-health scan"
  python3 scripts/skill_health.py scan || SKILL_SCAN=$?
  echo
fi

if [[ -f .grok/skills/cache-freshness-check/scripts/cache_freshness_check.py ]]; then
  echo ">> Cache freshness"
  python3 .grok/skills/cache-freshness-check/scripts/cache_freshness_check.py || true
  echo
fi

echo "=== Summary ==="
echo "skill_scan_exit=$SKILL_SCAN (1 means stale covers)"
echo "Next: /skill-health and /cache-freshness-check if flags; do not auto-fix at L1."
exit "$SKILL_SCAN"
