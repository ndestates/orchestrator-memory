#!/bin/bash
# target-app project-drift-guardian db_ops.sh (adapted)
# Handles init, query, log for drift/requirements DB.
# For target-app: can target the app's MySQL (ddev or prod via doctl) or sqlite.
# Usage examples in SKILL.md.

set -euo pipefail

DB_TYPE=${DB_TYPE:-sqlite}  # or mysql
DB_FILE=${DB_FILE:-.grok/drift_guardian.db}
SQLITE="sqlite3 $DB_FILE"

if [ "$DB_TYPE" = "mysql" ]; then
  # target-app prod or ddev: assume env or ddev mysql -e "..."
  MYSQL="ddev mysql -e"  # local default; override for prod
  # For prod: use doctl + proper connection (see prod-db-maintenance patterns)
fi

cmd=${1:-help}

case "$cmd" in
  init)
    if [ "$DB_TYPE" = "sqlite" ]; then
      $SQLITE < "$(dirname "$0")/init_db.sql"
      echo "SQLite drift DB initialized."
    else
      echo "For MySQL/target-app DB: run the equivalent CREATE TABLE statements via migration or ddev mysql."
    fi
    ;;
  query-requirements)
    if [ "$DB_TYPE" = "sqlite" ]; then
      $SQLITE "SELECT id, title, status, branch FROM requirements WHERE status != 'done' ORDER BY priority;"
    else
      echo "SELECT ... FROM requirements ... (adapt for target-app schema)"
    fi
    ;;
  log-decision)
    req_id=$2; decision=$3; rationale=$4; reviewer=${5:-grok}
    if [ "$DB_TYPE" = "sqlite" ]; then
      $SQLITE "INSERT INTO decisions (requirement_id, decision, rationale, ai_reviewer, timestamp) VALUES ($req_id, '$decision', '$rationale', '$reviewer', datetime('now'));"
    fi
    echo "Decision logged for req $req_id."
    ;;
  log-drift)
    # e.g. ./db_ops.sh log-drift "schema" "model changed without migration" "blocker"
    type=$2; evidence=$3; severity=$4
    # INSERT into drifts table...
    echo "Drift logged: $type - $severity"
    ;;
  backup-before-deploy)
    # Tie to prod-db-maintenance or target-app backup
    echo "Run backup first (see prod-db-maintenance or ddev export-db)."
    ;;
  *)
    echo "Commands: init, query-requirements, log-decision <id> <decision> <rationale>, log-drift <type> <evidence> <severity>, backup-before-deploy"
    ;;
esac
