#!/usr/bin/env bash
# Static bug-hunter scan — fast signals before deep agent review.
# Usage: bash .grok/skills/bug-hunter-agent/scripts/bug-hunter-scan.sh [ROOT]
# Writes JSON-ish summary to stdout; optional REPORT path as $2.

set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
REPORT="${2:-}"

section() { echo ""; echo "=== $1 ==="; }
count_grep() {
  local label="$1"
  local pattern="$2"
  local glob="${3:-*}"
  local n
  n=$(grep -rE --include="$glob" -n "$pattern" "$ROOT" 2>/dev/null \
    | grep -vE '/(vendor|node_modules|\.git|storage/framework|bootstrap/cache|dist|build)/' \
    | wc -l) || n=0
  echo "$label: $n"
  if [[ "$n" -gt 0 && "$n" -le 20 ]]; then
    grep -rE --include="$glob" -n "$pattern" "$ROOT" 2>/dev/null \
      | grep -vE '/(vendor|node_modules|\.git|storage/framework|bootstrap/cache|dist|build)/' \
      | head -20
  fi
}

echo "bug-hunter-scan root=$ROOT"
echo "timestamp=$(date -u +%Y-%m-%dT%H%M%SZ)"

section "Markers"
count_grep "TODO/FIXME/HACK" '(TODO|FIXME|HACK|XXX|BUG):' '*.{php,js,ts,tsx,vue,py,go,rs,md}'
count_grep "dd/dump die" '\b(dd|dump|var_dump|print_r|die\(|exit\()\s*\(' '*.php'
count_grep "console debug" 'console\.(log|debug|warn)\(' '*.{js,ts,tsx,vue}'

section "Security signals (triage only — use security-audit-agent for full review)"
count_grep "raw SQL concat" '(DB::raw|whereRaw|selectRaw|orderByRaw).*(\$|\.|\{)' '*.php'
count_grep "eval/exec" '\b(eval|exec|shell_exec|system|passthru)\s*\(' '*.{php,py,sh}'
count_grep "hardcoded secret pattern" '(password|api_key|secret|token)\s*=\s*['\''\"][^'\''\"]+['\''\"]' '*.{php,js,ts,env.example,yml,yaml}'

section "Error handling"
count_grep "empty catch" 'catch\s*\([^)]*\)\s*\{\s*\}' '*.php'
count_grep "suppress errors @" '@(include|require|file_get_contents)' '*.php'

section "Laravel hints (if present)"
if [[ -d "$ROOT/app" ]]; then
  count_grep "missing authorize in controller" 'function\s+(store|update|destroy)\s*\(' 'app/Http/Controllers/**/*.php' 2>/dev/null || true
  count_grep "DB::transaction missing near writes" '::create\(|::update\(|::delete\(' 'app/**/*.php'
fi

section "Tests"
if [[ -d "$ROOT/tests" ]]; then
  echo "test_files: $(find "$ROOT/tests" -name '*.php' 2>/dev/null | wc -l)"
  count_grep "skipped tests" '(markTestSkipped|->skip\()' 'tests/**/*.php'
else
  echo "test_files: 0 (no tests/ directory)"
fi

section "Config"
if [[ -f "$ROOT/.env.example" ]]; then
  echo ".env.example: present"
else
  echo ".env.example: MISSING"
fi

echo ""
echo "Scan complete. Deep review required — static grep produces false positives."

if [[ -n "$REPORT" ]]; then
  mkdir -p "$(dirname "$REPORT")"
  "$0" "$ROOT" 2>&1 | tee "$REPORT" >/dev/null
  echo "Wrote $REPORT"
fi