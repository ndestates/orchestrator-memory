#!/usr/bin/env python3
"""CLI: ensure project-manifest reflects this repo, not the orchestrator template.

Any agent/model that reads project-manifest (file or MCP get_project_manifest)
must run this check (or honor the identity field MCP returns) and surface
TEMPLATE_RESIDUE / WARN in the briefing.

Usage:
  python3 scripts/check-project-manifest.py
  python3 scripts/check-project-manifest.py --json
  python3 scripts/check-project-manifest.py --root /path/to/app

Exit codes:
  0  ok
  1  warn or template_residue or missing (non-fatal for session-start; agent must report)
  2  usage / internal error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _engine.manifest_identity import (  # noqa: E402
    check_manifest_identity,
    format_text_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check project-manifest identity (not template residue)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: git top-level or cwd)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON")
    args = parser.parse_args(argv)

    root = args.root
    if root is None:
        try:
            import subprocess

            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
            root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
        except Exception:
            root = Path.cwd()
    root = root.resolve()

    result = check_manifest_identity(root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        sys.stdout.write(format_text_report(result))

    status = result.get("status")
    if status == "ok":
        return 0
    if status in {"warn", "template_residue", "missing"}:
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
