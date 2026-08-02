#!/usr/bin/env bash
# Scaffold loop spine files on a target project when missing (wave apps).
set -euo pipefail

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"
ORCH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

scaffold() {
  local src="$1" dst="$2"
  if [[ -f "$TARGET/$dst" ]]; then
    echo "  skip (exists): $dst"
    return 0
  fi
  mkdir -p "$(dirname "$TARGET/$dst")"
  cp "$ORCH/$src" "$TARGET/$dst"
  echo "  scaffold: $dst"
}

echo "Scaffold loop spine → $TARGET"
scaffold "starters/loop-state/STATE.template.md" "STATE.md"
scaffold "starters/loop-state/loop-run-log.template.md" "loop-run-log.md"
scaffold "VISION.md" "VISION.md"
if [[ ! -f "$TARGET/reports/loops/lessons-state.json" ]]; then
  mkdir -p "$TARGET/reports/loops"
  cp "$ORCH/reports/loops/lessons-state.json" "$TARGET/reports/loops/lessons-state.json"
  echo "  scaffold: reports/loops/lessons-state.json"
fi
mkdir -p "$TARGET/reports/loops"
touch "$TARGET/reports/loops/.gitkeep" 2>/dev/null || true

# Secure vault graph ledger (append-only, hash-chained)
mkdir -p "$TARGET/reports/vault"
touch "$TARGET/reports/vault/.gitkeep" 2>/dev/null || true
if [[ ! -f "$TARGET/reports/vault/events.jsonl" ]]; then
  touch "$TARGET/reports/vault/events.jsonl"
  echo "  scaffold: reports/vault/events.jsonl (secure graph ledger)"
fi

echo "Done."