#!/usr/bin/env python3
"""Backward-compatible wrapper — use customize-skills-for-project.py instead."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUSTOMIZE = ROOT / "scripts" / "customize-skills-for-project.py"


def main() -> int:
    cmd = [
        sys.executable,
        str(CUSTOMIZE),
        "--project-root",
        str(ROOT),
        "--auto-profile",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())