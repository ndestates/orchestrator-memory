#!/usr/bin/env python3
"""Per-app compound gate for session-start — assess and optionally close learning loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow import from scripts/_engine when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _engine.app_compound import assess, close  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-app compound learning gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="App repo root")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--close",
        action="store_true",
        help="Close SCAFFOLD or unclosed_report via loop-compound (L1)",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    result = close(root) if args.close else assess(root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"status={result.get('status')} action={result.get('action')}")
        if result.get("state_lessons"):
            print("state_lessons:")
            for lesson in result["state_lessons"]:
                print(f"  - {lesson}")
    if args.close and not result.get("closed", True):
        return 1 if result.get("compound_exit", 0) not in (0, None) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())