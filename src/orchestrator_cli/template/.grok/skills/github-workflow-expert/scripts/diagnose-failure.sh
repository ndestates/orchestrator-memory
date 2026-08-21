#!/usr/bin/env bash
# diagnose-failure.sh — Analyze recent GitHub Actions failure for a workflow or run.
# Helps developers quickly find WHY it failed and HOW to fix it (no continual failures).
# Usage:
#   bash .grok/skills/github-workflow-expert/scripts/diagnose-failure.sh --workflow <name-or-file> [--limit 3]
#   bash .grok/skills/github-workflow-expert/scripts/diagnose-failure.sh --run <run-id>
#   bash .grok/skills/github-workflow-expert/scripts/diagnose-failure.sh   # auto latest failure

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI required (gh auth login)" >&2
  exit 1
fi

WORKFLOW=""
RUN_ID=""
LIMIT=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow|-w) WORKFLOW="$2"; shift 2 ;;
    --run|-r) RUN_ID="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

echo "=== GitHub Workflow Failure Diagnosis ==="
echo "Repo: $(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo ""

# Resolve workflow if name given
if [[ -n "$WORKFLOW" && "$WORKFLOW" != *.yml && "$WORKFLOW" != *.yaml ]]; then
  # try to map name to file
  wf_file=$(gh workflow list --json name,path -q '.[] | select(.name == "'"$WORKFLOW"'") | .path' 2>/dev/null || true)
  if [[ -n "$wf_file" ]]; then
    WORKFLOW="$wf_file"
  fi
fi

if [[ -z "$RUN_ID" ]]; then
  # Find latest failure
  if [[ -n "$WORKFLOW" ]]; then
    RUN_ID=$(gh run list --workflow="$WORKFLOW" --status=failure --limit=1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
  else
    RUN_ID=$(gh run list --status=failure --limit=1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
  fi
fi

if [[ -z "$RUN_ID" ]]; then
  echo "No recent failure found for ${WORKFLOW:-all workflows}."
  echo "Tip: gh run list --status failure"
  exit 0
fi

echo "Analyzing run: $RUN_ID"
echo ""

# Basic info
gh run view "$RUN_ID" --json conclusion,displayTitle,headBranch,workflowName,createdAt,updatedAt,url -q '
"Workflow: " + .workflowName + "\n" +
"Branch: " + .headBranch + "\n" +
"Conclusion: " + .conclusion + "\n" +
"Title: " + .displayTitle + "\n" +
"Time: " + .createdAt + " -> " + .updatedAt + "\n" +
"URL: " + .url
'

echo ""
echo "=== Failed Jobs + Log Excerpt (last 80 lines per failed job) ==="
gh run view "$RUN_ID" --log-failed | tail -n 200 || true

echo ""
echo "=== Common Failure Pattern Detection ==="

# Fetch raw log for analysis (gh run view --log-failed gives some)
LOG=$(gh run view "$RUN_ID" --log-failed 2>/dev/null | cat || true)

PATTERNS=()

if echo "$LOG" | grep -qiE "(secret|token|GH_TOKEN|DO_TOKEN|secrets\.) (not found|undefined|required|invalid|denied|permission)"; then
  PATTERNS+=("SECRET_OR_TOKEN_ISSUE: A secret or token is missing or insufficiently scoped.")
fi

if echo "$LOG" | grep -qiE "(permission|403|401|Resource not accessible by integration|write permission)"; then
  PATTERNS+=("PERMISSIONS_ISSUE: Workflow lacks required permissions: (contents, pull-requests, actions, etc.). Add top-level or job-level 'permissions:' block.")
fi

if echo "$LOG" | grep -qiE "(node|actions/setup-node|javascript|deprecat|18|20|24)"; then
  PATTERNS+=("NODE_VERSION_ISSUE: Likely Node 18/20 deprecation or missing FORCE_JAVASCRIPT_ACTIONS_TO_NODE24. Run scripts/verify_github_actions_node24.py and ensure env pin.")
fi

if echo "$LOG" | grep -qiE "(checkout|ref|sha|merge|rebase|pathspec)"; then
  PATTERNS+=("CHECKOUT_OR_REF_ISSUE: Checkout action or ref problem (often token scope or concurrent force-push). Check concurrency group and GITHUB_TOKEN permissions.")
fi

if echo "$LOG" | grep -qiE "(concurrency|cancelled|skipped|in-progress)"; then
  PATTERNS+=("CONCURRENCY_ISSUE: Runs are being cancelled by group. Set cancel-in-progress: false for critical promotion/CI workflows.")
fi

if echo "$LOG" | grep -qiE "(path|paths-ignore|workflow_dispatch|push:.*branches)"; then
  PATTERNS+=("TRIGGER_OR_PATH_FILTER_ISSUE: The push/PR did not match 'on:' triggers or path filters. Check .github/workflows and your changed files.")
fi

if echo "$LOG" | grep -qiE "(ddev|local only|command not found|artisan|composer)"; then
  PATTERNS+=("DDEV_OR_LOCAL_CMD_IN_CI: CI runs on ubuntu-latest (no DDEV by default). Move logic to pure ubuntu steps or use container job.")
fi

if [[ ${#PATTERNS[@]} -eq 0 ]]; then
  PATTERNS+=("UNKNOWN_PATTERN: Review full log above. Common next: run 'gh run view $RUN_ID --log-failed | grep -i error' and search for the first red line.")
fi

for p in "${PATTERNS[@]}"; do
  echo "  - $p"
done

echo ""
echo "=== Recommended Fixes (apply then re-validate + guardrails) ==="

echo "1. Validate the workflow file(s):"
echo "   bash .grok/skills/github-workflow-expert/scripts/workflow-validate.sh .github/workflows/*.yml"

echo ""
echo "2. If permissions/secret: edit the workflow to add explicit permissions and/or set secret."
echo "   Then: gh secret list --env production"
echo "   gh secret set THE_SECRET --env production"

echo ""
echo "3. If Node or validation: "
echo "   python3 scripts/verify_github_actions_node24.py"
echo "   (ensure FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 in env)"

echo ""
echo "4. After edits: use /git-workflow-guardrails to commit/push."
echo "   Then re-dispatch: gh workflow run <name> --ref $(git branch --show-current)"

echo ""
echo "5. Re-check:"
echo "   gh run list --workflow=<name> --limit 3"

echo ""
echo "Full run URL above. Paste any specific error line for deeper analysis."

# Also list recent runs for context
echo ""
echo "=== Recent runs for context ==="
if [[ -n "$WORKFLOW" ]]; then
  gh run list --workflow="$WORKFLOW" --limit "$LIMIT"
else
  gh run list --limit "$LIMIT"
fi

echo ""
echo "Diagnosis complete. Use the suggested edits + guardrails to stop the failure loop."
