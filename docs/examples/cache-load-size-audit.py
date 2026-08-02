#!/usr/bin/env python3
"""Rough load-cost proxy for cache vs anti-pattern files (chars / 4 ≈ tokens).

Usage (from repo root):
  python3 docs/examples/cache-load-size-audit.py

See docs/guides/cache-and-token-savings.md for interpretation.
Not a billing tool — relative comparison only.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Lean-friendly vs expensive loads (template defaults)
FILES = [
    ("lean", "docs/codebase/.codebase-freshness.txt"),
    ("lean", "docs/codebase/SECTIONS.md"),
    ("lean", "docs/codebase/README.md"),
    ("lean", "docs/codebase/ARCHITECTURE.md"),
    ("expensive", "docs/codebase/.codebase-scan.txt"),
    ("expensive", "chains/registry.yaml"),
]


def main() -> int:
    print(f"root={ROOT}")
    print(f"{'tier':<10} {'file':<45} {'chars':>8} {'~tok':>8}")
    lean = 0
    expensive = 0
    for tier, rel in FILES:
        p = ROOT / rel
        if not p.is_file():
            print(f"{tier:<10} {rel:<45} {'MISSING':>8}")
            continue
        n = len(p.read_text(encoding="utf-8", errors="replace"))
        tok = n // 4
        if tier == "lean":
            lean += tok
        else:
            expensive += tok
        print(f"{tier:<10} {rel:<45} {n:8d} {tok:8d}")
    print("---")
    print(f"sum ~tokens lean-listed:      {lean}")
    print(f"sum ~tokens expensive-listed: {expensive}")
    if lean:
        print(f"expensive / lean ratio:     {expensive / lean:.1f}x")
    print("Note: lean sessions load sections of listed lean files, not always full files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
