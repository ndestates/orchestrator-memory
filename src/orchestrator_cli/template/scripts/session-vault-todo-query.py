#!/usr/bin/env python3
"""Session-start: query vault using open items from the latest TODO file (v1.5.0+).

Extracts unchecked tasks from ``TODO/*_TODO.md`` (or latest ``TODO/*.md``),
builds a short query, and runs vault precedent search so agents do not re-plan
work the brain already recorded.

Usage:
  python3 scripts/session-vault-todo-query.py
  python3 scripts/session-vault-todo-query.py --json
  python3 scripts/session-vault-todo-query.py --todo TODO/2026-07-11_TODO.md

Exit 0 always (report-only); missing vault/TODO prints a one-line skip.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts._engine import vault as vault_mod
    from scripts._engine import vault_query as vault_query_mod
except ImportError:
    try:
        from _engine import vault as vault_mod  # type: ignore
        from _engine import vault_query as vault_query_mod  # type: ignore
    except ImportError:
        vault_mod = None  # type: ignore
        vault_query_mod = None  # type: ignore

DEFAULT_LEDGER = ROOT / "reports" / "vault" / "events.jsonl"
OPEN_RE = re.compile(r"^\s*[-*]\s+\[\s*\]\s+(.+)$")


def latest_todo(todo_dir: Path) -> Path | None:
    if not todo_dir.is_dir():
        return None
    files = sorted(todo_dir.glob("*.md"), key=lambda p: p.name, reverse=True)
    # Prefer dated *_TODO.md
    dated = [p for p in files if re.search(r"\d{4}-\d{2}-\d{2}", p.name)]
    pool = dated or files
    return pool[0] if pool else None


def open_items(todo_path: Path, *, limit: int = 12) -> list[str]:
    items: list[str] = []
    try:
        text = todo_path.read_text(encoding="utf-8")
    except OSError:
        return items
    for line in text.splitlines():
        m = OPEN_RE.match(line)
        if not m:
            continue
        body = m.group(1).strip()
        # strip trailing markdown links noise
        body = re.sub(r"\s*\(.*\)$", "", body).strip()
        if len(body) < 4:
            continue
        items.append(body[:160])
        if len(items) >= limit:
            break
    return items


def build_query(items: list[str], *, max_chars: int = 280) -> str:
    if not items:
        return ""
    # Prefer first 3–5 open items as keywords
    joined = " | ".join(items[:5])
    return joined[:max_chars]


def run_query(ledger: Path, query: str, *, limit: int = 3) -> dict[str, Any]:
    if vault_query_mod is None:
        return {"status": "no_engine", "precedents": [], "query": query}
    if not ledger.is_file() or ledger.stat().st_size == 0:
        return {"status": "no_ledger", "precedents": [], "query": query}
    try:
        return vault_query_mod.query_precedents(
            query, ledger_path=ledger, limit=limit, build_chain=False
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "precedents": [], "query": query}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--todo", type=Path, default=None, help="TODO file (default: latest under TODO/)")
    ap.add_argument("--todo-dir", type=Path, default=ROOT / "TODO")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    todo_path = args.todo or latest_todo(args.todo_dir)
    if not todo_path or not todo_path.is_file():
        msg = "Vault×TODO: no TODO file found — skip query."
        if args.json:
            print(json.dumps({"status": "no_todo", "message": msg}))
        else:
            print(msg)
        return 0

    items = open_items(todo_path)
    query = build_query(items)
    if not query:
        msg = f"Vault×TODO: no open items in {todo_path.name} — skip query."
        if args.json:
            print(json.dumps({"status": "no_open_items", "todo": str(todo_path), "message": msg}))
        else:
            print(msg)
        return 0

    if vault_mod is None:
        msg = "Vault×TODO: vault engine not importable — skip (deploy scripts/_engine)."
        if args.json:
            print(json.dumps({"status": "no_engine", "query": query, "message": msg}))
        else:
            print(msg)
        return 0

    result = run_query(args.ledger, query, limit=args.limit)
    precedents = result.get("precedents") or []

    payload = {
        "status": result.get("status", "ok"),
        "todo": str(todo_path),
        "open_items": items[:8],
        "query": query,
        "precedent_count": len(precedents),
        "precedents": [],
    }
    for p in precedents[: args.limit]:
        judgment = p.get("judgment") or p.get("text") or ""
        if isinstance(judgment, dict):
            judgment = json.dumps(judgment)[:160]
        payload["precedents"].append(
            {
                "judgment": str(judgment)[:200],
                "score": p.get("score") or p.get("similarity"),
                "type": p.get("type"),
            }
        )

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"Vault×TODO: query from {todo_path.name} ({len(items)} open item(s))")
    print(f"  Q: {query[:200]}")
    if not precedents:
        print("  → No close vault precedents — proceed carefully; do not invent prior work.")
        return 0
    print(f"  → {len(precedents)} precedent(s) — cite before re-planning:")
    for i, p in enumerate(payload["precedents"], 1):
        print(f"    P{i}: {p['judgment'][:180]}")
    print("  Rule: do not re-plan work the vault already records as done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
