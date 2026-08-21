#!/usr/bin/env bash
# Append chain completion to loop-run-log.md and refresh STATE.md last-chain section.
# Also notes secure vault graph head when present (self-building knowledge ledger).
# Usage:
#   bash scripts/chain-completion-write.sh \
#     --chain-id chain-health-watch \
#     --outcome PASS \
#     --cache "manifest,STATE,CHAIN" \
#     [--artifact reports/loops/2026-06-29-chain-health.md] \
#     [--steps "audit,verify"] \
#     [--branch feature/foo] \
#     [--next "Review open PRs"]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHAIN_ID=""
OUTCOME=""
CACHE=""
ARTIFACT="—"
STEPS="—"
BRANCH=""
NEXT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --chain-id) CHAIN_ID="${2:-}"; shift 2 ;;
    --outcome) OUTCOME="${2:-}"; shift 2 ;;
    --cache) CACHE="${2:-}"; shift 2 ;;
    --artifact) ARTIFACT="${2:-}"; shift 2 ;;
    --steps) STEPS="${2:-}"; shift 2 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --next) NEXT="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$CHAIN_ID" || -z "$OUTCOME" || -z "$CACHE" ]]; then
  echo "Required: --chain-id, --outcome, --cache" >&2
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git branch --show-current 2>/dev/null || echo 'unknown')"
fi

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_LOG="${ROOT}/loop-run-log.md"
STATE="${ROOT}/STATE.md"

if [[ ! -f "$RUN_LOG" ]]; then
  cat >"$RUN_LOG" <<'EOF'
# Loop Run Log (append-only)

| Timestamp (UTC) | Loop | Level | Cache cited | Outcome | Artifact |
|-----------------|------|-------|-------------|---------|----------|
EOF
fi

printf '| %s | %s | chain | %s | %s | %s |\n' \
  "$TS" "$CHAIN_ID" "$CACHE" "$OUTCOME" "$ARTIFACT" >>"$RUN_LOG"

python3 - "$STATE" "$TS" "$CHAIN_ID" "$OUTCOME" "$CACHE" "$ARTIFACT" "$STEPS" "$BRANCH" "$NEXT" <<'PY'
import sys
from pathlib import Path

state_path = Path(sys.argv[1])
ts, chain_id, outcome = sys.argv[2], sys.argv[3], sys.argv[4]
cache, artifact, steps, branch, next_action = sys.argv[5:10]

block = f"""## Last chain run

- **When:** {ts}
- **Chain:** {chain_id}
- **Branch:** {branch}
- **Outcome:** {outcome}
- **Steps:** {steps}
- **Cache cited:** {cache}
- **Artifact:** {artifact}
"""

# Secure vault graph head (if present) for self-building provenance
vault_ledger = Path("reports/vault/events.jsonl")
if vault_ledger.exists():
    try:
        last_line = vault_ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
        import json
        last_ev = json.loads(last_line)
        vh = last_ev.get("content_hash", "n/a")[:12]
        block += f"- **Vault head (secure graph):** {vh} (reports/vault/events.jsonl)\n"
    except Exception:
        pass

if next_action:
    block += f"- **Next:** {next_action}\n"

if state_path.exists():
    text = state_path.read_text()
else:
    text = "# Loop State (durable spine)\n\n"

marker = "## Last chain run"
if marker in text:
    before, rest = text.split(marker, 1)
    rest_lines = rest.splitlines()
    end = len(rest_lines)
    for i, line in enumerate(rest_lines[1:], start=1):
        if line.startswith("## ") and i > 0:
            end = i
            break
    text = before.rstrip() + "\n\n" + block.rstrip() + "\n\n" + "\n".join(rest_lines[end:]).lstrip()
else:
    if "## Last session" in text:
        text = text.replace("## Last session", block.rstrip() + "\n\n## Last session", 1)
    else:
        text = text.rstrip() + "\n\n" + block.rstrip() + "\n"

state_path.write_text(text)
PY

echo "Appended chain completion: $CHAIN_ID ($OUTCOME) → loop-run-log.md, STATE.md"