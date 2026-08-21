#!/usr/bin/env bash
# Host prep for workflow_dispatch run-chain: validate chain id, optional host snapshot, dispatch note.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHAIN_ID="${1:-}"
if [[ -z "$CHAIN_ID" ]]; then
  echo "Usage: bash scripts/run-chain-host.sh <chain_id>" >&2
  exit 1
fi

DATE="$(date -u +%Y-%m-%d)"
REPORT_DIR="reports/chains"
mkdir -p "$REPORT_DIR"
REPORT="${REPORT_DIR}/${DATE}-${CHAIN_ID}-dispatch.md"

python3 - "$CHAIN_ID" <<'PY' || exit 1
import sys, yaml
from pathlib import Path

chain_id = sys.argv[1]
data = yaml.safe_load(Path("chains/registry.yaml").read_text())
chains = {c["id"]: c for c in data.get("chains", [])}
if chain_id not in chains:
    print(f"Unknown chain id: {chain_id}", file=sys.stderr)
    sys.exit(1)
c = chains[chain_id]
print(f"OK: {chain_id} — {c.get('name')} ({len(c.get('steps', []))} steps)")
PY

HOST_MAP=(
  "cache-freshness-watch:scripts/loop-cache-freshness-host.sh"
  "chain-health-watch:scripts/loop-chain-health-host.sh"
  "github-ci-watch:scripts/loop-github-ci-host.sh"
  "repo-health-watch:scripts/loop-repo-health-host.sh"
  "loop-daily:scripts/loop-daily-triage-host.sh"
)

host_ran="(none)"
for entry in "${HOST_MAP[@]}"; do
  id="${entry%%:*}"
  script="${entry#*:}"
  if [[ "$CHAIN_ID" == "$id" && -f "$ROOT/$script" ]]; then
    bash "$ROOT/$script"
    host_ran="$script"
    break
  fi
done

chain_summary="$(python3 - "$CHAIN_ID" <<'PY'
import sys, yaml
from pathlib import Path
chain_id = sys.argv[1]
data = yaml.safe_load(Path("chains/registry.yaml").read_text())
for c in data.get("chains", []):
    if c["id"] == chain_id:
        steps = [f"{s.get('invoke')} ({s.get('type','skill')})" for s in c.get("steps", [])]
        print(f"name: {c.get('name')}")
        print(f"tier: {c.get('token_tier')}")
        print(f"steps: {', '.join(steps)}")
        break
PY
)"

cat >"$REPORT" <<EOF
# Chain Dispatch — ${DATE}

**Chain:** \`${CHAIN_ID}\`
**Trigger:** workflow_dispatch (\`run-chain.yml\`)
**Host prep:** \`${host_ran}\`

## Registry

\`\`\`
${chain_summary}
\`\`\`

## Agent steps (cache-first)

1. Load manifest + chain cache from \`chains/registry.yaml\`
2. Run \`/chain ${CHAIN_ID} scheduled\` (skips confirm when in \`chain_policy.scheduled_allowlist\`)
3. On completion: \`bash scripts/chain-completion-write.sh --chain-id ${CHAIN_ID} --outcome PASS --cache "<paths>" --artifact "<report>"\`
4. For watch chains: run \`/loop-verifier\` on the final artifact, then \`bash scripts/loop-compound.sh --report <artifact>\`

## Artifacts

- This dispatch note: \`${REPORT}\`
- Loop host snapshots (if any): \`reports/loops/*-host.md\`
EOF

echo "Wrote $REPORT"