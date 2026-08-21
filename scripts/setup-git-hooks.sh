#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push scripts/git-push-secrets-guard.py 2>/dev/null || true
bash scripts/ensure-git-secrets-hooks.sh

echo "Git hooks configured: core.hooksPath=.githooks"
echo "pre-commit: secrets/env guard + bundle-hash stamp auto-regen (+ optional app extensions)"
echo "pre-push: secrets/env guard on outgoing commits"
echo "  bypass stamp: ORCHESTRATOR_BUNDLE_HASH_SKIP=1"