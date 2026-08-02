#!/usr/bin/env bash
# Host snapshot for L1 security-flywheel-watch (CI cron / manual).
# Report-only. No auto-fix. No secrets.
# Same pattern as ndestates/lightstone interdependent flywheel watches.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-security-flywheel-host.md"
mkdir -p reports/loops reports/security

STATUS_ARGS=(--quick)
if [[ "${1:-}" == "--full" ]]; then
  STATUS_ARGS=()
fi
if [[ "${1:-}" == "--peers" ]] || [[ "${2:-}" == "--peers" ]]; then
  STATUS_ARGS+=(--peers)
fi

status_out="$(bash scripts/security-flywheel-status.sh "${STATUS_ARGS[@]}" 2>&1 || true)"
result_line="$(echo "$status_out" | grep -E '^RESULT=' || echo 'RESULT=UNKNOWN')"
pass_line="$(echo "$status_out" | grep -E '^PASS=' || true)"

branch="$(git branch --show-current 2>/dev/null || echo '(detached)')"
head_sha="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

cat >"$REPORT" <<EOF
# Security Flywheel Host Snapshot — ${DATE}

**Level:** L1 host-only (agent deepens via \`/chain security-flywheel\`)  
**Branch:** \`${branch}\` @ \`${head_sha}\`  
**Lifecycle:** find → triage → fix → ship → prevent ([SECURITY.md](../../SECURITY.md))  
**Doctrine:** [stronger-with-every-update](../../docs/reference/stronger-with-every-update.md) · [security-flywheel](../../docs/guides/security-flywheel.md)

## Status script output

\`\`\`
${status_out}
\`\`\`

## Operator notes

- ${result_line}
- ${pass_line:-PASS/WARN/FAIL counts in block above}
- Triage FAIL as **S0/S1** per SECURITY.md before ship.
- Interdependent apps (ndestates ↔ lightstone): \`bash scripts/security-flywheel-status.sh --peers\`
- Optional memory: \`orchestrator memory ingest --text "flywheel ${result_line}" --source flywheel\`

## Next

- Manual depth: \`/chain security-flywheel\`
- CE: \`/chain cyber-essentials-review\`
- Diff critic: \`/chain code-review\` when auth/MCP/upgrade surfaces touched
EOF

echo "wrote ${REPORT}"
echo "${result_line}"
exit 0
