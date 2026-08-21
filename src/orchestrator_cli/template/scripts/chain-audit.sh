#!/usr/bin/env bash
# Validate chains/registry.yaml: YAML parse, invoke targets exist, cache paths present.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT}/scripts/compose-registry.py" ]] && [[ -f "${ROOT}/chains/registry.template.yaml" ]]; then
  python3 "${ROOT}/scripts/compose-registry.py" >/dev/null 2>&1 || true
fi
REGISTRY="${ROOT}/chains/registry.yaml"
SCORE=0
MAX=100
ISSUES=0

fail() {
  echo "FAIL: $*"
  ISSUES=$((ISSUES + 1))
}

warn() {
  echo "WARN: $*"
}

ok() {
  echo "OK: $*"
}

if [[ ! -f "$REGISTRY" ]]; then
  fail "Missing $REGISTRY"
  exit 1
fi

python3 - "$REGISTRY" <<'PY' || fail "Invalid YAML in chains/registry.yaml"
import sys, yaml
yaml.safe_load(open(sys.argv[1]))
print("YAML parse OK")
PY

resolve_invoke() {
  local invoke="$1"
  local type="$2"
  case "$type" in
    skill)
      if [[ -f "${ROOT}/.grok/skills/${invoke}/SKILL.md" ]]; then
        return 0
      fi
      if [[ -f "${ROOT}/.grok/skills/${invoke//-agent/}/SKILL.md" ]]; then
        return 0
      fi
      if [[ -f "${ROOT}/.grok/agents/${invoke}.md" ]] || [[ -f "${ROOT}/.grok/agents/${invoke}-agent.md" ]]; then
        return 0
      fi
      return 1
      ;;
    prompt)
      if [[ -f "${ROOT}/.grok/prompts/${invoke}.md" ]]; then
        return 0
      fi
      if [[ -f "${ROOT}/.github/prompts/${invoke}.prompt.md" ]]; then
        return 0
      fi
      return 1
      ;;
    *)
      return 1
      ;;
  esac
}

while IFS= read -r chain_id; do
  [[ -z "$chain_id" ]] && continue
  steps=$(python3 - "$REGISTRY" "$chain_id" <<'PY'
import sys, yaml
data = yaml.safe_load(open(sys.argv[1]))
for c in data.get("chains", []):
    if c["id"] == sys.argv[2]:
        for s in c.get("steps", []):
            print(f"{s.get('type','skill')}|{s.get('invoke','')}")
        break
PY
)
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    type="${line%%|*}"
    invoke="${line#*|}"
    if resolve_invoke "$invoke" "$type"; then
      ok "chain ${chain_id}: ${type}/${invoke}"
      SCORE=$((SCORE + 5))
    else
      fail "chain ${chain_id}: missing ${type}/${invoke}"
    fi
  done <<< "$steps"
done < <(python3 - "$REGISTRY" <<'PY'
import yaml
for c in yaml.safe_load(open(__import__("sys").argv[1])).get("chains", []):
    print(c["id"])
PY
)

# Spot-check required cache paths (warn only)
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  full="${ROOT}/${path}"
  if [[ -e "$full" ]] || [[ "$path" == TODO/ ]] || [[ "$path" == *.md ]]; then
    ok "cache path exists or expected: ${path}"
  else
    warn "cache path missing (may be project-specific): ${path}"
  fi
done < <(python3 - "$REGISTRY" <<'PY'
import yaml
seen = set()
for c in yaml.safe_load(open(__import__("sys").argv[1])).get("chains", []):
    for p in c.get("cache_files_required", []):
        if p not in seen:
            seen.add(p)
            print(p)
PY
)

SCORE=$((SCORE > MAX ? MAX : SCORE))
echo ""
echo "Chain audit score: ${SCORE}/${MAX} (issues: ${ISSUES})"
[[ "$ISSUES" -eq 0 ]]