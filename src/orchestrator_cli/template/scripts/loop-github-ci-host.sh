#!/usr/bin/env bash
# Host snapshot for L1 github-ci-watch (CI cron).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-github-ci-host.md"
mkdir -p reports/loops

workflow_files="(no .github/workflows)"
if [[ -d .github/workflows ]]; then
  workflow_files="$(ls -1 .github/workflows/*.{yml,yaml} 2>/dev/null | xargs -n1 basename | paste -sd, - || ls -1 .github/workflows/)"
fi

wf_list="(gh not available)"
run_list="(gh not available)"
secret_list="(gh not available)"

if command -v gh >/dev/null 2>&1; then
  wf_list="$(gh workflow list 2>/dev/null || echo 'gh workflow list failed')"
  run_list="$(gh run list --limit 10 2>/dev/null || echo 'gh run list failed')"
  secret_list="$(gh secret list 2>/dev/null || echo 'gh secret list failed')"
  if gh secret list --env production >/dev/null 2>&1; then
    secret_list="${secret_list}

--- production env ---
$(gh secret list --env production 2>/dev/null || echo 'no production env')"
  fi
fi

failed_runs="(none or gh unavailable)"
if command -v gh >/dev/null 2>&1; then
  failed_runs="$(gh run list --limit 20 --json conclusion,displayTitle,workflowName,updatedAt \
    --jq '[.[] | select(.conclusion=="failure")] | .[0:5]' 2>/dev/null || echo '[]')"
fi

cat >"$REPORT" <<EOF
# GitHub CI Host Snapshot — ${DATE}

**Level:** L1 host-only (agent completes report via \`/chain github-ci-watch\`)

## Local workflow files

${workflow_files}

## gh workflow list

\`\`\`
${wf_list}
\`\`\`

## Recent runs (≤10)

\`\`\`
${run_list}
\`\`\`

## Failed runs (≤5, JSON)

\`\`\`json
${failed_runs}
\`\`\`

## Secret names (repo + production if present)

\`\`\`
${secret_list}
\`\`\`

## Next (human / agent)

1. Run \`/chain github-ci-watch\` per patterns/github-ci-watch.md
2. Write \`${DATE}-github-ci.md\` and update STATE.md
3. Run \`/loop-verifier\` on final artifact
EOF

echo "Wrote $REPORT"