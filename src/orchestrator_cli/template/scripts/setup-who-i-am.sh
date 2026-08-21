#!/usr/bin/env bash
# One-time (or refresh) operator profile setup for multi-AI persistent context.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TEMPLATE="${ROOT}/.grok/memories/who-i-am.template.md"
TARGET="${ROOT}/.grok/memories/who-i-am.md"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: missing $TEMPLATE" >&2
  exit 1
fi

if [[ -f "$TARGET" ]]; then
  echo "who-i-am: already exists at .grok/memories/who-i-am.md"
  echo "  Edit in place or remove and re-run to copy from template."
else
  cp "$TEMPLATE" "$TARGET"
  echo "who-i-am: created .grok/memories/who-i-am.md from template"
  echo "  Edit with your name, role, goals, and communication style."
fi

echo ""
echo "Next steps:"
echo "  1. Edit .grok/memories/who-i-am.md"
echo "  2. In session: /multi-ai-best-practices-setup (or load grok_usage_guide.md)"
echo "  3. Daily: /chain session-start (loads who-i-am when present)"
echo "  4. Other platforms: see docs/getting-started/who-i-am-setup.md"