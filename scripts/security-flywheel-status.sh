#!/usr/bin/env bash
# Security flywheel status — Chrome-style lifecycle dashboard (orchestrator template + apps).
# Stack-aware (generic + optional Laravel).
# Find-layer signals only (report). Does not auto-fix. No secrets printed.
#
# Usage:
#   bash scripts/security-flywheel-status.sh
#   bash scripts/security-flywheel-status.sh --json
#   bash scripts/security-flywheel-status.sh --quick   # skip long sweeps
#   bash scripts/security-flywheel-status.sh --peers   # check interdependent peer apps
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

JSON=0
QUICK=0
PEERS=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    --quick) QUICK=1 ;;
    --peers) PEERS=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
  esac
done

TS="$(date -u +%Y-%m-%dT%H:%MZ)"
OUT_DIR="reports/security"
mkdir -p "$OUT_DIR"
REPORT_MD="${OUT_DIR}/flywheel-status-$(date -u +%Y-%m-%d).md"

pass=0
warn=0
fail=0
declare -a LINES=()

record() {
  local stage="$1" status="$2" detail="$3"
  LINES+=("${stage}|${status}|${detail}")
  case "$status" in
    PASS) pass=$((pass + 1)) ;;
    WARN) warn=$((warn + 1)) ;;
    FAIL) fail=$((fail + 1)) ;;
  esac
}

# ── FIND: doctrine + trust map ─────────────────────────────────
if [[ -f SECURITY.md ]]; then
  record "find.security_md" "PASS" "SECURITY.md present (trust boundaries)"
else
  record "find.security_md" "FAIL" "SECURITY.md missing"
fi

if [[ -f docs/guides/security-flywheel.md ]]; then
  record "find.flywheel_guide" "PASS" "docs/guides/security-flywheel.md present"
else
  record "find.flywheel_guide" "WARN" "flywheel guide missing"
fi

if [[ -f docs/reference/stronger-with-every-update.md ]]; then
  record "find.stronger_standard" "PASS" "stronger-with-every-update standard present"
else
  record "find.stronger_standard" "WARN" "stronger-with-every-update doc missing"
fi

if grep -q 'stronger_with_every_update:\s*true' .github/project-manifest.yaml 2>/dev/null \
  || grep -q 'stronger_with_every_update:\s*true' .grok/project-manifest.yaml 2>/dev/null; then
  record "find.manifest_flag" "PASS" "security_policy.stronger_with_every_update true"
else
  record "find.manifest_flag" "WARN" "manifest flag stronger_with_every_update not true"
fi

# ── FIND: continuous signals ───────────────────────────────────
if [[ -f .github/dependabot.yml ]] || [[ -f .github/dependabot.yaml ]]; then
  record "find.dependabot" "PASS" "Dependabot config present"
else
  record "find.dependabot" "WARN" "dependabot.yml missing"
fi

if [[ -f scripts/git-push-secrets-guard.py ]]; then
  record "ship.secrets_guard" "PASS" "git-push-secrets-guard.py present"
else
  record "ship.secrets_guard" "WARN" "secrets guard script not found"
fi

if [[ -f scripts/mcp-threat-scan.sh ]] || [[ -f scripts/mcp-threat-scan.py ]]; then
  record "find.mcp_threat_scan" "PASS" "mcp-threat-scan present"
else
  record "find.mcp_threat_scan" "WARN" "mcp-threat-scan missing"
fi

if [[ -f scripts/session-security-sweep.sh ]]; then
  if [[ "$QUICK" -eq 0 ]]; then
    sweep_out="$(bash scripts/session-security-sweep.sh 2>&1 || true)"
    if echo "$sweep_out" | grep -q 'overall=PASS'; then
      record "find.session_sweep" "PASS" "session-security-sweep overall=PASS"
    elif echo "$sweep_out" | grep -q 'overall=WARN'; then
      record "find.session_sweep" "WARN" "session-security-sweep overall=WARN"
    elif echo "$sweep_out" | grep -q 'overall=FAIL'; then
      record "find.session_sweep" "FAIL" "session-security-sweep overall=FAIL"
    else
      record "find.session_sweep" "WARN" "session-security-sweep ran; overall not parsed"
    fi
  else
    record "find.session_sweep" "PASS" "skipped (--quick)"
  fi
else
  record "find.session_sweep" "WARN" "session-security-sweep.sh missing"
fi

if [[ -f reports/security/bundle-hashes.json ]]; then
  record "ship.bundle_hash" "PASS" "bundle-hashes.json present"
else
  record "ship.bundle_hash" "WARN" "bundle-hashes stamp missing"
fi

# ── PREVENT: template / host ───────────────────────────────────
if [[ -f scripts/memory_agent.py ]] || [[ -f src/orchestrator_cli/commands/memory.py ]]; then
  record "prevent.always_on_memory" "PASS" "always-on memory CLI present"
else
  record "prevent.always_on_memory" "WARN" "memory agent not on this tip"
fi

if [[ -f reports/vault/events.jsonl ]] || [[ -f scripts/_engine/vault.py ]]; then
  record "prevent.vault" "PASS" "vault engine/ledger available"
else
  record "prevent.vault" "WARN" "vault not detected"
fi

if grep -q 'security-flywheel' chains/registry.yaml 2>/dev/null; then
  record "prevent.flywheel_chain" "PASS" "chain security-flywheel registered"
else
  record "prevent.flywheel_chain" "WARN" "register /chain security-flywheel"
fi

if grep -q 'SECURITY.md' chains/registry.yaml 2>/dev/null \
  || grep -q 'security-flywheel' chains/registry.yaml 2>/dev/null; then
  record "prevent.security_md_critic" "PASS" "chains reference security flywheel / SECURITY.md"
else
  record "prevent.security_md_critic" "WARN" "wire SECURITY.md into code-review / flywheel"
fi

# MCP off-by-default (template product default)
if grep -qE 'mcp:\s*"?off"?' .github/project-manifest.yaml 2>/dev/null \
  || grep -qE 'mcp:\s*"?off"?' .grok/project-manifest.yaml 2>/dev/null; then
  record "prevent.mcp_off_default" "PASS" "runtime.mcp defaults off"
else
  record "prevent.mcp_off_default" "WARN" "MCP default not clearly off"
fi

# ── Laravel app signals ──────────────────────────────────────────
if [[ -f artisan ]] || [[ -f config/security.php ]]; then
  record "find.laravel_app" "PASS" "Laravel-style app detected"
  if [[ -f config/security.php && -f app/Http/Middleware/SecurityHeaders.php ]]; then
    record "prevent.headers" "PASS" "SecurityHeaders + config/security.php"
  elif [[ -f config/security.php ]]; then
    record "prevent.headers" "WARN" "config/security.php without SecurityHeaders middleware path"
  else
    record "prevent.headers" "WARN" "security headers stack not detected"
  fi
  if [[ -f config/security.php ]] && grep -qE "CSP_ENABLED" config/security.php 2>/dev/null; then
    record "prevent.csp_config" "PASS" "CSP config present"
  else
    record "prevent.csp_config" "WARN" "CSP config not detected (app)"
  fi
  if grep -rq 'isRequired:\s*true' app/Providers/Filament 2>/dev/null \
    || grep -rq 'isRequired: true' app/Providers/Filament 2>/dev/null; then
    record "prevent.admin_mfa" "PASS" "Filament MFA isRequired true signal"
  else
    record "prevent.admin_mfa" "WARN" "admin MFA required flag not detected"
  fi
else
  record "find.laravel_app" "PASS" "not a Laravel app tip (template/generic OK)"
fi

# ── Interdependent peers (optional yaml, --peers only) ────────
check_peer() {
  local peer_path="$1" peer_name="$2"
  if [[ ! -d "$peer_path" ]]; then
    record "peer.${peer_name}" "WARN" "peer path missing: ${peer_path}"
    return
  fi
  if [[ -f "${peer_path}/SECURITY.md" ]]; then
    record "peer.${peer_name}.security_md" "PASS" "${peer_name} SECURITY.md present"
  else
    record "peer.${peer_name}.security_md" "WARN" "${peer_name} SECURITY.md missing"
  fi
  if [[ -f "${peer_path}/docs/guides/security-flywheel.md" ]] \
    || [[ -f "${peer_path}/scripts/security-flywheel-status.sh" ]]; then
    record "peer.${peer_name}.flywheel" "PASS" "${peer_name} flywheel surface present"
  else
    record "peer.${peer_name}.flywheel" "WARN" "${peer_name} flywheel not detected"
  fi
}

# Peers: ONLY when --peers (never because yaml ships in-tree — that was a fleet leak).
# Default product posture: active project only; do not walk ~/projects or siblings.
if [[ "$PEERS" -eq 1 ]]; then
  if [[ -f scripts/security/flywheel-peers.yaml ]]; then
    # Parse simple "path:" lines under peers (no yaml lib required)
    while IFS= read -r line; do
      if [[ "$line" =~ path:[[:space:]]*(.+) ]]; then
        p="${BASH_REMATCH[1]}"
        p="${p//\"/}"
        p="${p//\'/}"
        # resolve relative to ROOT
        if [[ "$p" != /* ]]; then
          p="${ROOT}/${p}"
        fi
        name="$(basename "$p")"
        check_peer "$p" "$name"
      fi
    done < scripts/security/flywheel-peers.yaml
  else
    record "peer.config" "WARN" "no scripts/security/flywheel-peers.yaml"
  fi
fi

# ── write report ───────────────────────────────────────────────
{
  echo "# Security flywheel status"
  echo
  echo "- Generated: \`${TS}\`"
  echo "- Branch: \`$(git branch --show-current 2>/dev/null || echo unknown)\`"
  echo "- HEAD: \`$(git rev-parse --short HEAD 2>/dev/null || echo unknown)\`"
  echo "- Mode: $([ "$QUICK" -eq 1 ] && echo quick || echo full)$([ "$PEERS" -eq 1 ] && echo '+peers' || true)"
  echo "- Lifecycle: find → triage → fix → ship → prevent"
  echo
  echo "| Stage key | Status | Detail |"
  echo "|-----------|--------|--------|"
  for row in "${LINES[@]}"; do
    IFS='|' read -r st status detail <<<"$row"
    echo "| \`${st}\` | **${status}** | ${detail} |"
  done
  echo
  echo "**PASS=${pass} WARN=${warn} FAIL=${fail}**"
  echo
  echo "Next: triage FAIL as S0/S1 per SECURITY.md; run \`/chain security-flywheel\` for CE + audit depth."
  echo "Peers: \`bash scripts/security-flywheel-status.sh --peers\` · Guide: docs/guides/security-flywheel.md"
  echo "Memory: optional \`orchestrator memory ingest --text \"flywheel status PASS/WARN/FAIL\" --source flywheel\`"
} >"$REPORT_MD"

if [[ "$JSON" -eq 1 ]]; then
  python3 - <<PY
import json
rows = """$(printf '%s\n' "${LINES[@]}")""".strip().splitlines()
items = []
for r in rows:
    if not r.strip():
        continue
    parts = r.split("|", 2)
    if len(parts) == 3:
        items.append({"key": parts[0], "status": parts[1], "detail": parts[2]})
print(json.dumps({
    "generated": "${TS}",
    "pass": ${pass},
    "warn": ${warn},
    "fail": ${fail},
    "report_path": "${REPORT_MD}",
    "items": items,
}, indent=2))
PY
else
  echo "=== Security flywheel status (${TS}) ==="
  for row in "${LINES[@]}"; do
    IFS='|' read -r st status detail <<<"$row"
    printf '%-4s  %-36s  %s\n' "$status" "$st" "$detail"
  done
  echo
  echo "PASS=${pass} WARN=${warn} FAIL=${fail}"
  echo "report_path=${REPORT_MD}"
  echo
  if [[ "$fail" -gt 0 ]]; then
    echo "RESULT=FAIL — triage S0/S1 before ship"
    exit 1
  elif [[ "$warn" -gt 0 ]]; then
    echo "RESULT=WARN — review warnings; S2 track in TODO"
    exit 0
  else
    echo "RESULT=PASS"
    exit 0
  fi
fi
