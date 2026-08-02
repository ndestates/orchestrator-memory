#!/usr/bin/env python3
"""Idempotently add push-secrets-guard job to .github/workflows/ci.yml."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
MARKER = "push-secrets-guard:"
JOB = """
  push-secrets-guard:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Scan changed files for secrets and blocked env paths
        run: |
          set -euo pipefail
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            range="${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }}"
          elif [[ "${{ github.event.before }}" == "0000000000000000000000000000000000000000" ]]; then
            range="${{ github.sha }}"
          else
            range="${{ github.event.before }}..${{ github.sha }}"
          fi
          python3 scripts/git-push-secrets-guard.py --range "${range}"
"""


def main() -> int:
    if not CI.is_file():
        print(f"skip: no {CI.relative_to(ROOT)}")
        return 0

    text = CI.read_text(encoding="utf-8")
    if MARKER in text:
        print("OK: push-secrets-guard job already present")
        return 0

    if "jobs:" not in text:
        print(f"ERROR: {CI} missing jobs: block", file=sys.stderr)
        return 1

    updated = text.rstrip() + JOB + "\n"
    CI.write_text(updated, encoding="utf-8")
    print(f"patched: added push-secrets-guard job to {CI.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())