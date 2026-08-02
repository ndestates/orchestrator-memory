#!/usr/bin/env bash
# Host snapshot for L1 cache-freshness-watch (CI cron). Agent completes synthesis separately.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-cache-freshness-host.md"
CHECKER=".grok/skills/cache-freshness-check/scripts/cache_freshness_check.py"
mkdir -p reports/loops

json_out="(checker missing)"
text_out="(checker missing)"
if [[ -f "$CHECKER" ]]; then
  json_out="$(python3 "$CHECKER" --json 2>/dev/null || echo '{"error":"checker failed"}')"
  text_out="$(python3 "$CHECKER" 2>/dev/null || echo 'checker failed')"
fi

cat >"$REPORT" <<EOF
# Cache Freshness Host Snapshot — ${DATE}

**Level:** L1 host-only (agent completes report via \`/chain cache-freshness-watch\`)

## Checker output (text)

\`\`\`
${text_out}
\`\`\`

## Checker output (JSON)

\`\`\`json
${json_out}
\`\`\`

## Next (human / agent)

1. Run \`/cache-freshness-check\` or \`/chain cache-freshness-watch\` per patterns/cache-freshness-watch.md
2. Write \`${DATE}-cache-freshness.md\` and update STATE.md
3. Run \`/loop-verifier\` on final artifact
EOF

echo "Wrote $REPORT"