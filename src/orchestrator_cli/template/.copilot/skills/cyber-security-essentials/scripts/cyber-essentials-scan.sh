#!/usr/bin/env bash
# cyber-essentials-scan.sh — static signals for UK Cyber Essentials code/config slice
# Run from repo root. Report-only; exit 0 always (findings are stdout).
#
# Excludes scanner sources, reports, vendor, node_modules, and virtualenvs
# so pattern strings / third-party examples do not self-match.

set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "=== Cyber Essentials static scan ==="
echo "root: $(pwd)"
echo "date: $(date -u +%Y-%m-%dT%H:%MZ)"
echo

ce_section() { echo "--- $1 ---"; }

# Paths that must never contribute findings (self / generated / deps)
_RG_GLOBS=(
  -g '!.git'
  -g '!vendor'
  -g '!node_modules'
  -g '!.local'
  -g '!.venv'
  -g '!venv'
  -g '!**/.venv/**'
  -g '!**/venv/**'
  -g '!**/site-packages/**'
  -g '!**/dist/**'
  -g '!reports/security/**'
  -g '!**/.grok/skills/cyber-security-essentials/scripts/**'
  -g '!**/scripts/session-security-sweep.sh'
  -g '!**/*cyber-essentials-scan.sh'
)

_GREP_EXCLUDE=(
  --exclude-dir=.git
  --exclude-dir=vendor
  --exclude-dir=node_modules
  --exclude-dir=.local
  --exclude-dir=.venv
  --exclude-dir=venv
  --exclude-dir=site-packages
  --exclude-dir=dist
  --exclude-dir=reports
  --exclude='*cyber-essentials-scan.sh'
  --exclude='session-security-sweep.sh'
)

# 2. Secure configuration — secrets & debug (real config/app sources only)
ce_section "Control 2: Secure configuration (secrets/debug)"
if command -v rg >/dev/null 2>&1; then
  hits="$(
    rg -n --hidden "${_RG_GLOBS[@]}" \
      -e 'APP_DEBUG\s*=\s*true' \
      -e 'APP_ENV\s*=\s*local' \
      -e '(password|api[_-]?key|secret|private[_-]?key)\s*=\s*['\''\"][^'\''\"]{8,}' \
      --glob '*.env' --glob '*.env.*' --glob '*.php' --glob '*.py' --glob '*.js' --glob '*.ts' \
      --glob '*.yaml' --glob '*.yml' --glob '*.json' \
      2>/dev/null | head -30 || true
  )"
  if [[ -n "${hits}" ]]; then
    echo "${hits}"
  else
    echo "(no matches)"
  fi
else
  hits="$(
    grep -RInE 'APP_DEBUG\s*=\s*true|password\s*=\s*['\''\"]' . \
      "${_GREP_EXCLUDE[@]}" \
      --include='*.env' --include='*.php' --include='*.py' --include='*.js' --include='*.ts' \
      --include='*.yaml' --include='*.yml' 2>/dev/null | head -20 || true
  )"
  if [[ -n "${hits}" ]]; then
    echo "${hits}"
  else
    echo "(no matches)"
  fi
fi
echo

# 1. Firewalls — CORS / bind
ce_section "Control 1: Firewalls (CORS / wide bind)"
if command -v rg >/dev/null 2>&1; then
  hits="$(
    rg -n "${_RG_GLOBS[@]}" \
      -e 'allowedOrigins.*\*' -e '0\.0\.0\.0' -e 'cors.*\*' \
      --glob '*.php' --glob '*.js' --glob '*.ts' --glob '*.yml' --glob '*.yaml' --glob '*.env*' \
      2>/dev/null | head -20 || true
  )"
  if [[ -n "${hits}" ]]; then
    echo "${hits}"
  else
    echo "(no matches)"
  fi
else
  echo "(rg not available — skipped; install: bash scripts/install-host-tools.sh --yes)"
fi
echo

# 3. User access control — auth surface
ce_section "Control 3: User access control (auth hints)"
if command -v rg >/dev/null 2>&1; then
  hits="$(
    rg -n "${_RG_GLOBS[@]}" \
      -e 'withoutMiddleware' -e '->withoutMiddleware' -e 'canAccessPanel' \
      -e 'authorize\(' -e 'Gate::' -e 'Policy' \
      --glob '*.php' 2>/dev/null | head -25 || true
  )"
  if [[ -n "${hits}" ]]; then
    echo "${hits}"
  else
    echo "(no php or no matches)"
  fi
else
  echo "(rg not available — skipped; install: bash scripts/install-host-tools.sh --yes)"
fi
echo

# 4. Malware / supply chain
ce_section "Control 4: Malware protection (lockfiles / uploads)"
for f in composer.lock package-lock.json pnpm-lock.yaml yarn.lock requirements.txt Pipfile.lock; do
  [[ -f "$f" ]] && echo "OK lockfile: $f" || true
done
if command -v rg >/dev/null 2>&1; then
  rg -n "${_RG_GLOBS[@]}" \
    -e 'getClientOriginalExtension|storeAs|move_uploaded' --glob '*.php' 2>/dev/null | head -15 || true
fi
echo

# 5. Security update management
ce_section "Control 5: Security update management"
if [[ -f .github/dependabot.yml ]]; then
  echo "OK: .github/dependabot.yml"
else
  echo "WARN: no dependabot.yml"
fi
[[ -f composer.json ]] && echo "hint: run composer audit (in DDEV for Laravel projects)"
[[ -f package.json ]] && echo "hint: run npm audit"
echo

ce_section "CI security signals"
for w in .github/workflows/*.yml .github/workflows/*.yaml; do
  [[ -f "$w" ]] || continue
  if grep -qE 'gitguardian|security|audit|dependabot' "$w" 2>/dev/null; then
    echo "OK workflow signal: $w"
  fi
done
echo
echo "=== Scan complete (review manually; not a certification tool) ==="
