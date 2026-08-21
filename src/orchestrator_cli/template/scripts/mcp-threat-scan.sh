#!/usr/bin/env bash
# MCP / agent instruction threat scan for orchestrator template.
# FAIL CLOSED (v1.6.0+): critical pattern hits exit 1 unless allowlisted.
#
# Usage:
#   bash scripts/mcp-threat-scan.sh [OUT_DIR]
#   ORCHESTRATOR_THREAT_SCAN_WARN_ONLY=1 bash scripts/mcp-threat-scan.sh  # legacy soft mode
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-$ROOT/reports/security}"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$OUT_DIR/mcp-threat-${TS}.txt"
RAW="$OUT_DIR/mcp-threat-${TS}.raw.txt"
: > "$OUT"
: > "$RAW"

cd "$ROOT"

ALLOWLIST="${ROOT}/scripts/security/threat-scan-allowlist.txt"

# Never scan vendor / cache trees (noise: pydantic/mcp "no validation" docs).
# Matched as path segments in grep output (path:line:...).
EXCLUDE_SEGMENTS=(
  '/.venv/'
  '/venv/'
  '/node_modules/'
  '/__pycache__/'
  '/.tox/'
  '/.mypy_cache/'
  '/site-packages/'
  '.dist-info/'
  '/.git/'
)

# Critical: active instruction / capability language (fail closed)
critical_patterns=(
  'ignore (previous|all|safety|rules|instructions)'
  'bypass (safety|security|validation|guardrails|hooks|secrets.guard)'
  'disable (security|audit|protection|secrets.guard|pre-commit|pre-push)'
  'exfiltrate (secrets|credentials|keys|env|tokens)'
  'send (secrets|credentials|api.keys|tokens) to'
  'run (any|arbitrary|untrusted) (code|script|command|shell)'
  'arbitrary (code|command) execution'
  'curl[^\n]{0,80}\|\s*(ba)?sh'
  'wget[^\n]{0,80}\|\s*(ba)?sh'
)

# Soft: review only (do not fail CI alone)
soft_patterns=(
  'no (sandbox|validation|auth|permission)'
  'exfiltrat(e|ion)|data exfil'
)

scan_dirs=(.grok .github .claude mcp-server scripts chains patterns)
includes=(
  --include='SKILL.md'
  --include='*.agent.md'
  --include='*.prompt.md'
  --include='copilot-instructions.md'
  --include='CLAUDE.md'
  --include='*.py'
  --include='*.sh'
  --include='*.yml'
  --include='*.yaml'
)

# rg globs (preferred — never enters excluded trees)
rg_globs=(
  --glob '!**/.venv/**'
  --glob '!**/venv/**'
  --glob '!**/node_modules/**'
  --glob '!**/__pycache__/**'
  --glob '!**/.tox/**'
  --glob '!**/.mypy_cache/**'
  --glob '!**/site-packages/**'
  --glob '!**/*.dist-info/**'
  --glob '!**/.git/**'
  --glob 'SKILL.md'
  --glob '*.agent.md'
  --glob '*.prompt.md'
  --glob 'copilot-instructions.md'
  --glob 'CLAUDE.md'
  --glob '*.py'
  --glob '*.sh'
  --glob '*.yml'
  --glob '*.yaml'
)

is_vendor_path() {
  local line="$1"
  # Normalize: ensure we can match /segment/ on paths without leading slash noise
  local p="/${line%%:*}/"
  local seg
  for seg in "${EXCLUDE_SEGMENTS[@]}"; do
    if [[ "$p" == *"$seg"* ]] || [[ "$line" == *"$seg"* ]]; then
      return 0
    fi
  done
  return 1
}

is_allowlisted() {
  local line="$1"
  # Scanner / linter / guardrail self-tests embed threat strings as fixtures
  case "$line" in
    scripts/orchestrator-malware-lint.py:*|scripts/mcp-threat-scan.sh:*|scripts/security/*|scripts/session-guardrails-check.py:*|scripts/_engine/untrusted_text.py:*)
      return 0
      ;;
  esac
  [[ -f "$ALLOWLIST" ]] || return 1
  while IFS= read -r rule || [[ -n "$rule" ]]; do
    [[ -z "$rule" || "$rule" =~ ^# ]] && continue
    if [[ "$line" == *"$rule"* ]]; then
      return 0
    fi
  done < "$ALLOWLIST"
  return 1
}

# Emit matching lines for a pattern (path:line:content), excluding vendor trees.
# IMPORTANT: always include the file path. `rg -I` / `--no-filename` is FORBIDDEN —
# without paths, allowlist + vendor exclusion cannot match and CI fails closed on
# scanner self-hits and site-packages noise.
scan_pattern() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    # -n line numbers · -H always path · --no-heading one line per hit
    # Do NOT pass -I/--no-filename.
    rg -n -H --no-heading -e "$pattern" "${rg_globs[@]}" "${scan_dirs[@]}" 2>/dev/null || true
  else
    grep -RInE "${includes[@]}" -e "$pattern" "${scan_dirs[@]}" 2>/dev/null | while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" ]] && continue
      is_vendor_path "$line" && continue
      printf '%s\n' "$line"
    done || true
  fi
}

crit_hits=0
soft_hits=0

for pattern in "${critical_patterns[@]}"; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    # Defense in depth if rg ever includes a path
    is_vendor_path "$line" && continue
    if is_allowlisted "$line"; then
      echo "ALLOW $line" >> "$OUT"
      continue
    fi
    echo "CRIT  $line" >> "$OUT"
    echo "$line" >> "$RAW"
    crit_hits=$((crit_hits + 1))
  done < <(scan_pattern "$pattern")
done

for pattern in "${soft_patterns[@]}"; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    is_vendor_path "$line" && continue
    if is_allowlisted "$line"; then
      continue
    fi
    echo "SOFT  $line" >> "$OUT"
    soft_hits=$((soft_hits + 1))
  done < <(scan_pattern "$pattern")
done

{
  echo "=== MCP/agent threat scan $TS ==="
  echo "critical_hits=$crit_hits soft_hits=$soft_hits"
  echo "report=$OUT"
  echo "vendor_excluded=yes"
} | tee -a "$OUT"

if [[ "$crit_hits" -gt 0 ]]; then
  echo "FAIL: $crit_hits critical threat pattern hit(s). See $OUT" >&2
  if [[ "${ORCHESTRATOR_THREAT_SCAN_WARN_ONLY:-}" == "1" ]]; then
    echo "WARN_ONLY set — not failing CI" >&2
    exit 0
  fi
  exit 1
fi

if [[ "$soft_hits" -gt 0 ]]; then
  echo "OK with soft notes: $soft_hits informational hit(s) (non-blocking)."
else
  echo "No MCP/agent threat patterns detected." | tee -a "$OUT"
fi
exit 0
