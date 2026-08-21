#!/usr/bin/env bash
# Host snapshot for L1 daily triage (CI or cron). Cache files only — no source scan.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATE="$(date -u +%Y-%m-%d)"
REPORT="reports/loops/${DATE}-triage-host.md"
mkdir -p reports/loops

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
status="$(git status --short 2>/dev/null | head -20 || true)"
todo_file="none"
if compgen -G "TODO/*.md" >/dev/null 2>&1; then
  todo_file="$(ls -1 TODO/*.md | tail -1)"
fi
scan_marker="missing"
if [[ -f docs/codebase/.codebase-scan.txt ]]; then
  scan_marker="$(grep -E 'Last full scan|First run|^Generated:' docs/codebase/.codebase-scan.txt 2>/dev/null | head -2 | tr '\n' '; ' || true)"
fi

pr_block="(gh not available)"
if command -v gh >/dev/null 2>&1; then
  pr_block="$(gh pr list --limit 5 2>/dev/null || echo 'gh pr list failed')"
fi

run_block="(skipped)"
if command -v gh >/dev/null 2>&1; then
  run_block="$(gh run list --limit 3 2>/dev/null || echo 'gh run list failed')"
fi

audit_out=""
if bash scripts/loop-audit.sh >/tmp/loop-audit.txt 2>&1; then
  audit_out="$(tail -5 /tmp/loop-audit.txt)"
else
  audit_out="$(cat /tmp/loop-audit.txt)"
fi

cat >"$REPORT" <<EOF
# Daily Triage Host Snapshot — ${DATE}

**Level:** L1 host-only (agent completes cache synthesis separately)

## Cache pointers (agent must load — not duplicated here)

- LOOP.md, STATE.md, loop-budget.md
- docs/codebase/README.md, CONCERNS.md (sections)
- Latest TODO: ${todo_file}
- .codebase-scan: ${scan_marker}

## Host snapshot

- **Branch:** ${branch}
- **git status (≤20 lines):**
\`\`\`
${status}
\`\`\`

## Open PRs (≤5)

\`\`\`
${pr_block}
\`\`\`

## Recent workflow runs (≤3)

\`\`\`
${run_block}
\`\`\`

## Loop audit

\`\`\`
${audit_out}
\`\`\`

## Next (human / agent)

1. Run \`/loop-triage\` with cache-first load per patterns/daily-triage.md
2. Merge host snapshot into \`${DATE}-triage.md\` if needed
3. Run \`/loop-verifier\` on final artifact
EOF

echo "Wrote $REPORT"