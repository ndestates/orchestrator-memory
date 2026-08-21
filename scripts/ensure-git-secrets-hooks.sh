#!/usr/bin/env bash
# Ensure secrets/env guard is wired into githooks without clobbering app-specific pre-commit logic.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p .githooks
chmod +x scripts/git-push-secrets-guard.py 2>/dev/null || true

if [[ ! -f .githooks/pre-push ]]; then
  cat > .githooks/pre-push <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
if [[ "${GIT_PUSH_SECRETS_BYPASS:-}" == "1" ]]; then
  echo "pre-push: WARNING — secrets/env guard bypassed (GIT_PUSH_SECRETS_BYPASS=1)"
  exit 0
fi
failed=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [[ "${local_sha}" == "0000000000000000000000000000000000000000" ]] && continue
  if [[ "${remote_sha}" == "0000000000000000000000000000000000000000" ]]; then
    range="${local_sha}"
  else
    range="${remote_sha}..${local_sha}"
  fi
  python3 scripts/git-push-secrets-guard.py --range "${range}" || failed=1
done
exit "${failed}"
EOF
  chmod +x .githooks/pre-push
else
  chmod +x .githooks/pre-push
fi

MARKER='git-push-secrets-guard.py --staged'
if [[ ! -f .githooks/pre-commit ]]; then
  cat > .githooks/pre-commit <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
if [[ "${GIT_PUSH_SECRETS_BYPASS:-}" != "1" ]]; then
  python3 scripts/git-push-secrets-guard.py --staged || exit 1
fi
if [[ -x "scripts/guard-auth-stability.sh" ]]; then
  scripts/guard-auth-stability.sh
fi
EOF
  chmod +x .githooks/pre-commit
elif ! grep -qF "$MARKER" .githooks/pre-commit; then
  tmp="$(mktemp)"
  cat > "$tmp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
if [[ "${GIT_PUSH_SECRETS_BYPASS:-}" != "1" ]]; then
  python3 scripts/git-push-secrets-guard.py --staged || exit 1
fi
EOF
  cat .githooks/pre-commit >> "$tmp"
  mv "$tmp" .githooks/pre-commit
  chmod +x .githooks/pre-commit
fi