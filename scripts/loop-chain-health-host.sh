#!/usr/bin/env bash
# Host snapshot for L1 chain-health-watch (CI cron).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-chain-health-host.md"
mkdir -p reports/loops

audit_out=""
audit_exit=0
if bash scripts/chain-audit.sh >/tmp/chain-audit-host.txt 2>&1; then
  audit_out="$(cat /tmp/chain-audit-host.txt)"
else
  audit_exit=$?
  audit_out="$(cat /tmp/chain-audit-host.txt)"
fi

registry_chains="$(python3 - <<'PY' 2>/dev/null || echo "(parse failed)"
import yaml
from pathlib import Path
data = yaml.safe_load(Path("chains/registry.yaml").read_text())
chains = data.get("chains") or []
print(f"chains: {len(chains)}")
for c in chains[:15]:
    print(f"  - {c.get('id')}")
if len(chains) > 15:
    print(f"  ... +{len(chains)-15} more")
PY
)"

cat >"$REPORT" <<EOF
# Chain Health Host Snapshot — ${DATE}

**Level:** L1 host-only (agent completes report via \`/chain chain-health-watch\`)

## Registry summary

\`\`\`
${registry_chains}
\`\`\`

## chain-audit.sh (exit ${audit_exit})

\`\`\`
${audit_out}
\`\`\`

## Next (human / agent)

1. Run \`/chain chain-health-watch\` per patterns/chain-health-watch.md
2. Write \`${DATE}-chain-health.md\` and update STATE.md
3. Run \`/loop-verifier\` on final artifact
EOF

echo "Wrote $REPORT"