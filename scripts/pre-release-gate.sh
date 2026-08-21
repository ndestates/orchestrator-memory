#!/usr/bin/env bash
# pre-release-gate.sh — mandatory checks before tagging a release.
# Fail-closed: any non-zero step aborts. Run from repo root.
#
# Usage:
#   bash scripts/pre-release-gate.sh
#   bash scripts/pre-release-gate.sh --skip-slow   # skip license e2e (local only)
#
# Wired into .github/workflows/release.yml — do not ship without this green.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SKIP_SLOW=0
for arg in "$@"; do
  case "$arg" in
    --skip-slow) SKIP_SLOW=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
  esac
done

step() {
  printf '\n======== %s ========\n' "$1"
}

fail() {
  printf 'PRE-RELEASE GATE FAILED: %s\n' "$1" >&2
  exit 1
}

step "1/8 Tooling tests (pytest)"
export PYTHONPATH="scripts:src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m pytest tests -q --tb=line || fail "pytest"

step "2/8 Chain audit"
bash scripts/chain-audit.sh || fail "chain-audit"

step "3/8 Template decontamination scan"
bash scripts/scan-template-contamination.sh || fail "contamination"

step "4/8 Malware / hostile-content lint"
python3 scripts/orchestrator-malware-lint.py || fail "malware-lint"

step "5/8 MCP / agent threat scan"
bash scripts/mcp-threat-scan.sh || fail "mcp-threat-scan"

step "6/8 Skill tool-governance"
python3 scripts/orchestrator-skill-governance.py || fail "skill-governance"

step "7/8 Session security sweep + CSE (active repo)"
# Report-only script exits 0; treat overall=FAIL as gate failure
sweep_out="$(bash scripts/session-security-sweep.sh --active-only 2>&1 || true)"
printf '%s\n' "$sweep_out" | tail -40
overall="$(printf '%s\n' "$sweep_out" | sed -n 's/^overall=//p' | head -1)"
if [[ "${overall}" == "FAIL" ]]; then
  fail "session-security-sweep overall=FAIL (secrets guard)"
fi
# CSE self-match regression: zero code hits expected on clean template
if printf '%s\n' "$sweep_out" | grep -qE 'session-security-sweep\.sh:[0-9]+:|cyber-essentials-scan\.sh:[0-9]+:'; then
  fail "CSE/security scan self-matched its own sources (false positive regression)"
fi

step "8/8 Bundle hash generate + verify"
python3 scripts/orchestrator-bundle-hash.py generate || fail "bundle-hash generate"
python3 scripts/orchestrator-bundle-hash.py verify || fail "bundle-hash verify"

if [[ "${SKIP_SLOW}" -eq 0 ]]; then
  step "Bonus: License e2e (mock)"
  export PYTHONPATH="mcp-server/src:src${PYTHONPATH:+:$PYTHONPATH}"
  python3 -m pytest mcp-server/tests/test_license.py -q --tb=line || fail "license e2e"
fi

step "9/9 VERSION alignment (SSOT + mirrors)"
ver="$(tr -d 'v \n\r' < VERSION)"
[[ -n "$ver" ]] || fail "VERSION empty"
# Comprehensive check (stamp, package.json, bundle-hashes)
if [[ -f scripts/check-version-alignment.py ]]; then
  python3 scripts/check-version-alignment.py || fail "version alignment (run: node scripts/npm/sync-version.js && python3 scripts/orchestrator-bundle-hash.py)"
else
  if [[ -f package.json ]]; then
    pkg_ver="$(python3 -c 'import json; print(json.load(open("package.json"))["version"])' 2>/dev/null || true)"
    if [[ -n "$pkg_ver" && "$pkg_ver" != "$ver" ]]; then
      fail "package.json version ($pkg_ver) != VERSION ($ver) — run: node scripts/npm/sync-version.js"
    fi
  fi
  stamp_file="scripts/orchestrator-template-version"
  if [[ ! -f "$stamp_file" ]]; then
    fail "missing $stamp_file (must mirror VERSION for deployed apps)"
  fi
  stamp="$(tr -d 'v \n\r' < "$stamp_file")"
  if [[ "$stamp" != "$ver" ]]; then
    fail "stamp $stamp_file ($stamp) != VERSION ($ver) — run: node scripts/npm/sync-version.js"
  fi
  echo "VERSION=$ver package.json=${pkg_ver:-n/a} stamp=$stamp ✓"
fi

printf '\n======== PRE-RELEASE GATE PASS ========\n'
printf 'Safe to tag when VERSION matches intended release.\n'
cat VERSION 2>/dev/null | sed 's/^/VERSION=/'
