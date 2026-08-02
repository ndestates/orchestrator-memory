#!/usr/bin/env python3
"""CLI wrapper for local Ollama detection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _engine.ollama_detect import evaluate, format_text  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect local Ollama install and API")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    report = evaluate(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        sys.stdout.write(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())