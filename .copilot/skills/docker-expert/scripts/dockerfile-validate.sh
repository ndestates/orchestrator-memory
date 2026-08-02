#!/usr/bin/env bash
# Lightweight Dockerfile hardening checks (orchestrator template).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
FILE="${1:-Dockerfile}"
[[ -f "$FILE" ]] || FILE="$ROOT/Dockerfile"
[[ -f "$FILE" ]] || { echo "FAIL: no Dockerfile at $FILE"; exit 1; }

TEXT="$(cat "$FILE")"
ISSUES=0
warn() { echo "WARN: $*"; }
fail() { echo "FAIL: $*"; ISSUES=$((ISSUES + 1)); }
ok() { echo "OK: $*"; }

echo "Validating: $FILE"

if grep -qiE 'FROM\s+ubuntu[^-]' <<<"$TEXT" && ! grep -qi 'AS build' <<<"$TEXT"; then
  fail "full ubuntu base in runtime — use alpine/distroless/slim"
fi

if ! grep -qiE 'AS\s+(build|builder|vendor|assets|production|prod|runtime)' <<<"$TEXT"; then
  warn "no named build stages — prefer multi-stage"
fi

if ! grep -qiE '^USER\s+' <<<"$TEXT"; then
  fail "missing USER directive (non-root required for production)"
fi

if grep -qiE 'COPY\s+\.env|ADD\s+\.env' <<<"$TEXT"; then
  fail ".env copied into image"
fi

if [[ ! -f "$(dirname "$FILE")/.dockerignore" ]] && [[ ! -f "$ROOT/.dockerignore" ]]; then
  fail "missing .dockerignore alongside Dockerfile"
else
  ok ".dockerignore present"
fi

if grep -qi ':latest' <<<"$TEXT"; then
  warn "uses :latest tag — pin digest or minor version"
fi

if [[ "$ISSUES" -eq 0 ]]; then
  echo "Result: PASS (warnings may remain)"
  exit 0
fi
echo "Result: FAIL ($ISSUES issue(s))"
exit 1