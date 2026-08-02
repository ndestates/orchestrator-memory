#!/usr/bin/env bash
# Loop readiness audit — cache-first infrastructure check (no agent required).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

score=0
max=210
notes=()

check() {
  local path="$1"
  local points="$2"
  if [[ -e "$path" ]]; then
    score=$((score + points))
    notes+=("OK  $path (+$points)")
  else
    notes+=("MISS $path (0)")
  fi
}

check "VISION.md" 8
check "LOOP.md" 10
check "STATE.md" 10
check "reports/loops/lessons-state.json" 5
check "patterns/compound-learning.md" 5
check "loop-budget.md" 10
check "loop-run-log.md" 5
check "patterns/registry.yaml" 10
check "patterns/daily-triage.md" 10
check "patterns/cache-freshness-watch.md" 3
check "patterns/chain-health-watch.md" 3
check "patterns/github-ci-watch.md" 3
check "patterns/repo-health-watch.md" 3
check ".grok/skills/loop-triage/SKILL.md" 10
check ".grok/skills/loop-verifier/SKILL.md" 10
check ".grok/skills/loop-engineering/SKILL.md" 5
check ".grok/skills/loop-compound/SKILL.md" 8
check ".grok/skills/app-compound-gate/SKILL.md" 5
check "scripts/loop-compound.sh" 3
check "scripts/loop_compound.py" 3
check "scripts/app_compound_gate.py" 3
check "patterns/app-compound-gate.md" 3
check "scripts/scaffold-loop-state.sh" 2
check "starters/loop-state/STATE.template.md" 2
check ".grok/skills/cache-efficient/SKILL.md" 5
check ".grok/skills/load-project-cache-first/SKILL.md" 5
check "scripts/wave-apps.sh" 2
check "scripts/loop-daily-triage-host.sh" 5
check "scripts/loop-cache-freshness-host.sh" 2
check "scripts/loop-chain-health-host.sh" 2
check "scripts/loop-github-ci-host.sh" 2
check "scripts/loop-repo-health-host.sh" 2
check "scripts/chain-completion-write.sh" 2
check "scripts/run-chain-host.sh" 2
check ".github/workflows/loop-daily-triage.yml" 10
check ".github/workflows/loop-weekly-watch.yml" 5
check ".github/workflows/run-chain.yml" 3
check "reports/loops" 5

if grep -q 'loop_policy:' .github/project-manifest.yaml 2>/dev/null; then
  score=$((score + 5))
  notes+=("OK  loop_policy in manifest (+5)")
else
  notes+=("MISS loop_policy in manifest (0)")
fi

if grep -q 'cache_first_mandatory: true' .github/project-manifest.yaml 2>/dev/null; then
  score=$((score + 5))
  notes+=("OK  cache_first_mandatory (+5)")
else
  notes+=("MISS cache_first_mandatory (0)")
fi

if grep -q 'compound_learning: true' .github/project-manifest.yaml 2>/dev/null; then
  score=$((score + 5))
  notes+=("OK  compound_learning in manifest (+5)")
else
  notes+=("MISS compound_learning (0)")
fi

echo "# Loop Readiness Audit"
echo
echo "Score: $score / $max"
echo
for n in "${notes[@]}"; do echo "- $n"; done
echo
if [[ "$score" -ge 80 ]]; then
  echo "Result: READY (≥80) — safe to enable scheduled L1 triage"
  exit 0
else
  echo "Result: NOT READY — fix misses before enabling schedule"
  exit 1
fi