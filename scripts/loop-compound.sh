#!/usr/bin/env bash
# Compound learning closure (steps 10–14): lessons → STATE + lessons-state.json + objective gates.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/loop_compound.py" --root "$ROOT" "$@"