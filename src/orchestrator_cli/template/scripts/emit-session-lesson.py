#!/usr/bin/env python3
"""Emit one session lesson into the vault brain (compound-style, secure).

Usage:
  python3 scripts/emit-session-lesson.py "Lesson text here" --source session:2026-07-07
  python3 scripts/emit-session-lesson.py --file reports/loops/my-report.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts._engine import vault as vmod  # noqa: E402

DEFAULT_LEDGER = Path("reports/vault/events.jsonl")


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a session lesson to vault")
    parser.add_argument("lesson", nargs="?", help="Lesson text")
    parser.add_argument("--file", type=Path, help="Read lesson from file (first ## Lessons section or whole)")
    parser.add_argument("--source", default="session:manual")
    parser.add_argument("--area", default="learning")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = args.lesson or ""
    if args.file:
        raw = args.file.read_text(encoding="utf-8")
        if "## Lessons" in raw:
            text = raw.split("## Lessons", 1)[1].split("##", 1)[0].strip()
        else:
            text = raw.strip()[:500]

    text = text.strip()
    if not text:
        print("No lesson text.", file=sys.stderr)
        return 1

    ledger = Path(args.ledger)
    events = vmod.load_events(ledger)
    prev = events[-1].get("content_hash") if events else None
    ev = vmod.secure_compound_emit(
        lesson=text,
        report_source=args.source,
        ledger_path=ledger,
        previous_head=prev,
        area=args.area,
    )
    if not ev:
        print("Lesson scrubbed to empty; not emitted.", file=sys.stderr)
        return 1

    ok, issues = vmod.verify_ledger(ledger)
    out = {"emitted": ev, "verify_ok": ok, "issues": issues[:2]}
    if args.json:
        import json
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"Vault learned: lesson id={ev.get('id')} area={args.area}")
        print(f"  verify={'PASS' if ok else 'FAIL'}")
        print(f"  text: {text[:100]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())