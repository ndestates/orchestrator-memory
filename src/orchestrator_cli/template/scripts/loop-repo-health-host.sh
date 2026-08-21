#!/usr/bin/env bash
# Host snapshot for L1 repo-health-watch (CI cron).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-repo-health-host.md"
mkdir -p reports/loops

current_branch="$(git branch --show-current 2>/dev/null || echo '(detached)')"
status_sb="$(git status -sb 2>/dev/null || echo 'git status failed')"

develop_diverge="(unavailable)"
master_diverge="(unavailable)"
if git rev-parse --verify origin/develop >/dev/null 2>&1; then
  develop_diverge="$(git rev-list --left-right --count origin/develop...develop 2>/dev/null || echo 'count failed')"
fi
if git rev-parse --verify origin/master >/dev/null 2>&1; then
  master_diverge="$(git rev-list --left-right --count origin/master...master 2>/dev/null || echo 'count failed')"
fi

stale_branches="$(git branch -vv 2>/dev/null | grep ': gone]' | head -20 || true)"
if [[ -z "$stale_branches" ]]; then
  stale_branches="(none detected)"
fi

pr_list="(gh not available)"
merged_recent="(gh not available)"
if command -v gh >/dev/null 2>&1; then
  pr_list="$(gh pr list --limit 10 2>/dev/null || echo 'gh pr list failed')"
  merged_recent="$(gh pr list --state merged --limit 5 2>/dev/null || echo 'gh pr list merged failed')"
fi

cat >"$REPORT" <<EOF
# Repo Health Host Snapshot — ${DATE}

**Level:** L1 host-only (agent completes report via \`/chain repo-health-watch\`)

## Branch

- **Current:** \`${current_branch}\`

\`\`\`
${status_sb}
\`\`\`

## Divergence (behind|ahead origin...local)

| Branch | behind|ahead |
|--------|----------|
| develop | ${develop_diverge} |
| master | ${master_diverge} |

## Stale local branches (gone upstream, ≤20)

\`\`\`
${stale_branches}
\`\`\`

## Open PRs (≤10)

\`\`\`
${pr_list}
\`\`\`

## Recent merges (≤5)

\`\`\`
${merged_recent}
\`\`\`

## Next (human / agent)

1. Run \`/chain repo-health-watch\` per patterns/repo-health-watch.md
2. Write \`${DATE}-repo-health.md\` and run \`bash scripts/chain-completion-write.sh\`
3. Run \`/loop-verifier\` on final artifact
EOF

echo "Wrote $REPORT"