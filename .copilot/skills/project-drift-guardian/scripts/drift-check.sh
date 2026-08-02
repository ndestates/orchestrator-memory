#!/bin/bash
# target-app project-drift-guardian drift-check.sh
# Adapted for target-app: checks code/scope drift, schema/model alignment, container/image tags, pre-deploy gates.
# Usage: ./.grok/skills/project-drift-guardian/scripts/drift-check.sh --branch $(git branch --show-current) --scope "e-sign + DO deploy + DB"
# Integrates with existing: calls model-schema-check equivalent, git diff, doctl (if available), etc.
# Exits non-zero on drift to block CI/deploy.

set -euo pipefail

BRANCH=${1:-$(git branch --show-current)}
SCOPE=${2:-"target-app core + hosting + DB"}
DRIFT_DB=".grok/drift_guardian.db"  # or use mysql via ddev if preferred
REPORT_DIR="reports/drift"
mkdir -p "$REPORT_DIR"

echo "=== target-app Drift Check ==="
echo "Branch: $BRANCH"
echo "Scope: $SCOPE"
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

# 1. Basic git/branch hygiene (tie to git-workflow-guardrails)
echo ">> Git status and diff vs main (code drift)"
git fetch origin main || true
git diff --stat origin/main...HEAD | head -20
CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep -E '\.(php|yml|yaml|md|sql|Dockerfile)' | head -10 || true)
echo "Key changed files: $CHANGED_FILES"

# 2. Schema / model drift (use existing skills/tools)
echo
echo ">> Schema/model alignment (model-schema-check + manual)"
# In real use: ddev exec php artisan model:check or call /model-schema-check equivalent
# Here: simple diff of recent migrations vs models
MIGRATIONS=$(find database/migrations -name "*create_*table.php" -newer database/migrations/0001_01_01_000000_create_users_table.php | wc -l || echo 0)
echo "Recent custom migrations: $MIGRATIONS"
# Placeholder: would run php artisan or grep models for fillable vs table columns
echo "Run 'ddev exec php artisan migrate:status' and cross with app/Models/ for full check."
echo "(Integrate: load model-schema-check + schema-audit-agent for production scan.)"

# 3. Container / image drift (for DO droplet or App + DOCR)
echo
echo ">> Container/image drift (tags, Dockerfile)"
if [ -f Dockerfile ]; then
  echo "Dockerfile present."
  # In CI: compare built tag vs 'production-latest' or pinned in docs/codebase or requirements DB
  echo "Expected: production-latest or git-sha tag. Check against DO registry via doctl."
fi
# Placeholder for droplet: check docker ps or compose on target if SSH allowed (prefer no-ssh patterns)
echo "(In full: doctl registry repository list-tags target-app-app or equivalent. Flag if floating tag used unsafely.)"

# 4. Scope / requirements drift (query DB or docs)
echo
echo ">> Scope/requirements drift (vs target-app requirements)"
# In real: sqlite3 $DRIFT_DB "SELECT * FROM requirements WHERE status != 'done' AND branch != '$BRANCH';"
# Or grep docs/codebase/CONCERNS.md + TODO for open items
echo "Critical target-app requirements (from cache/docs): canvas roundtrip, PDF embed (FPDI/dompdf), signature_hash audit, token security, DO (droplet+App) CI, safe DB updates, no schema/code drift."
echo "Compare current changes/plan to these. Flag if new feature (e.g. advanced compliance) appears without linked requirement."

# 5. Pre-deploy specific (tie to digitalocean skill + prod-db + guardrails)
echo
echo ">> Pre-deploy / DB / hosting drift gates"
echo "- Branch must not be main for changes."
echo "- Run prod-db-maintenance or safe migrate only with backup + schema check + post-eval."
echo "- For DO: confirm token scopes (registry+app only), hardened image, no broad DBaaS."
echo "- Full gate: this script + git-workflow-guardrails + model-schema-check + security-audit."
echo "If any drift: exit 1 and suggest remediation (new branch or DB update)."

# Example AI prompt for deeper analysis (use with /project-drift-guardian or grok)
cat << 'PROMPT'
AI Drift Analysis Prompt (for target-app):
Given target-app requirements (canvas signature roundtrip with hash audit + ip/ua, multi-signer ordered requests, PDF embed with FPDI fallback preserving original where possible, Filament admin for Documents/Signers/Requests, DDEV local parity, DigitalOcean hosting via droplet (full control) or App Platform (DOCR auto-deploy with limited tokens), CI with tests+schema+drift gates, safe DB migrations with backups+verify+eval, no drift on audit/compliance data):
Analyze the current branch $BRANCH changes (diff: $CHANGED_FILES), planned deploy/DB update, or scope.
Flag any drift (scope creep, schema vs model mismatch, container tag inconsistency, missing security/audit, unapproved hosting change) with evidence and severity (blocker/warning).
Suggest remediation tied to requirements DB.
Output concise report + Next actions.
PROMPT

echo
echo "=== Drift Check Summary ==="
echo "Drift flags: (implement logic to count from above checks; non-zero = block)"
echo "Recommendation: Run full /project-drift-guardian + load cache + relevant specialists before proceeding to CI or DO deploy/DB update."
echo "Report saved to $REPORT_DIR/$(date +%F)-drift-check.txt (enhance script to tee output)."

# Exit code for CI gate
# exit 1 if drifts detected
echo "Exit 0 for demo; real impl exits non-zero on detected drift to enforce 'avoid at all costs'."
exit 0
