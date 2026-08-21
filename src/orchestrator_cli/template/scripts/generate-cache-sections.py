#!/usr/bin/env python3
"""Generate docs/codebase/SECTIONS.md — heading index for grep-before-read."""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "docs" / "codebase"
OUT = CACHE_DIR / "SECTIONS.md"
SKIP = {".codebase-scan.txt", "SECTIONS.md"}


def headings(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
        if m:
            lines.append((len(m.group(1)), m.group(2).strip()))
    return lines


def one_line_summary(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("["):
            return s[:120]
    return "(see file)"


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [
        "# Cache section index",
        "",
        f"[GENERATED {ts}] — run `python3 scripts/generate-cache-sections.py` to refresh.",
        "",
        "Grep a heading here, then `Read` that section only. Never load `.codebase-scan.txt` in lean mode.",
        "",
    ]

    for path in sorted(CACHE_DIR.glob("*.md")):
        if path.name in SKIP:
            continue
        rel = f"docs/codebase/{path.name}"
        parts.append(f"## `{path.name}`")
        parts.append(f"- Summary: {one_line_summary(path)}")
        hs = headings(path)
        if hs:
            parts.append("- Sections:")
            for level, title in hs[:40]:
                indent = "  " * (level - 1)
                parts.append(f"  {indent}- {title}")
            if len(hs) > 40:
                parts.append(f"  - … +{len(hs) - 40} more headings")
        parts.append("")

    for path in sorted(CACHE_DIR.glob("*.txt")):
        if path.name == ".codebase-scan.txt":
            continue
        parts.append(f"## `{path.name}`")
        parts.append(f"- Lean spine file (read whole file, ≤35 lines)")
        parts.append("")

    OUT.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(parts)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())