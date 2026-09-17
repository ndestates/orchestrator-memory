#!/usr/bin/env bash
# OPTIONAL / LEGACY — set GitHub Actions secret VSCE_PAT for CLI vsce publish.
#
# Preferred ship path (match vscode-grok4): package VSIX in CI, upload via
# Marketplace manage UI (Visual Studio Code product type). No PAT required.
# Global Azure DevOps PATs retire 1 Dec 2026; do not treat this as production.
#
# The token is an Azure DevOps PAT (Marketplace Manage) — NOT a GitHub token.
#
# Usage (only if you still want opt-in CI publish):
#   bash scripts/set-vsce-pat.sh
#   bash scripts/set-vsce-pat.sh --repo ndestates/orchestrator-memory
#   VSCE_PAT='…' bash scripts/set-vsce-pat.sh   # non-interactive
#
set -euo pipefail

REPO="${REPO:-ndestates/orchestrator-memory}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! command -v gh >/dev/null; then
  echo "ERROR: gh CLI required" >&2
  exit 1
fi

if [[ -n "${VSCE_PAT:-}" ]]; then
  TOKEN="$VSCE_PAT"
else
  echo "Publisher: ndestates  ·  Repo: $REPO"
  echo
  echo "Create/reset an Azure DevOps PAT:"
  echo "  1. https://dev.azure.com  → profile → Personal access tokens → New Token"
  echo "  2. Organization: All accessible organizations (recommended)"
  echo "  3. Scopes: Custom → Marketplace → Acquire + Manage"
  echo "  4. Copy the token (shown once)"
  echo
  echo -n "Paste Azure DevOps PAT (input hidden), then Enter: "
  # shellcheck disable=SC2162
  read -r -s TOKEN
  echo
fi

if [[ -z "${TOKEN// }" ]]; then
  echo "ERROR: empty token" >&2
  exit 1
fi

# Do not echo token
printf '%s' "$TOKEN" | gh secret set VSCE_PAT --repo "$REPO"
unset TOKEN
echo "OK: VSCE_PAT set/updated on $REPO (Actions secret)."
echo
echo "Next:"
echo "  gh workflow run vscode-marketplace.yml -f version=2.1.0 --repo $REPO"
echo "  # or after merge: git tag v2.1.0 && git push origin v2.1.0"
echo
gh secret list --repo "$REPO" 2>/dev/null || true
